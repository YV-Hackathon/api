import json
import pandas as pd
from pathlib import Path
from utils.model import build_mappings
from utils.save_or_load import load_artifacts
import torch.nn.functional as F

model_path = Path("artifacts","model_1759812063")

# Load the model and encoders
model, user_enc, pastor_enc, pastor_trait_ids, _, _ = load_artifacts(model_path)

# Load the data to rebuild trait2idx (same as training)
ratings_path = Path("data","pastor_ratings.csv").resolve()
pastor_path = Path("data","pastor_traits.csv").resolve()
rating_df = pd.read_csv(ratings_path)
pastor_df = pd.read_csv(pastor_path)

# Rebuild the mappings to get trait2idx
user2idx, pastor2idx, trait2idx, pastor_trait_ids = build_mappings(rating_df, pastor_df)

import torch

# Exact, canonical pairs (word-for-word)
CANONICAL_TRAIT_PAIRS = [
    ("Verse-by-verse", "Topic-based"),
    ("Bible view: Strict inerrancy", "Bible view: Salvation-scope inerrancy"),
    ("Charismatic", "Non-charismatic"),
    ("Deep teaching", "Practical"),
    ("Energetic", "Calm"),
    ("Newcomer-friendly", "Member-focused"),
    ("Worship: Band-led", "Worship: Hymns/Choir-led"),
    ("Short sermons", "Long sermons"),
]

TRAIT_LIST = {t for pair in CANONICAL_TRAIT_PAIRS for t in pair}


def validate_one_per_pair(traits: list[str]) -> None:
    s = set(traits)
    if len(traits) != len(s):
        dupes = [x for x in traits if traits.count(x) > 1]
        raise ValueError(f"Duplicate trait(s) not allowed: {sorted(set(dupes))}")
    if not s.issubset(TRAIT_LIST):
        bad = sorted([x for x in traits if x not in TRAIT_LIST])
        raise ValueError(f"Unknown trait(s): {bad}")
    # Ensure exactly one pick from each pair
    for a, b in CANONICAL_TRAIT_PAIRS:
        count = int(a in s) + int(b in s)
        if count != 1:
            raise ValueError(f"Expected exactly one of {{{a} | {b}}}, got {count}")

def traits_to_trait_ids(traits: list[str], trait2idx: dict[str, int]) -> list[int]:
    try:
        return [trait2idx[t] for t in traits]
    except KeyError as e:
        raise KeyError(f"Trait not in trained trait2idx: {e.args[0]}")

def build_preference_vector_p(trait_ids: list[int], model, device=None) -> torch.Tensor:
    if device is None:
        device = next(model.parameters()).device
    idx = torch.tensor(trait_ids, dtype=torch.long, device=device)
    # Mean of selected trait embeddings (same as your EmbeddingBag 'mean')
    emb = model.trait_bag.weight.index_select(0, idx)  # (n_traits, d)
    return emb.mean(dim=0)  # (d,)

# ----- Use with your JSON -----
json_from_user = {
  "trait_choices": [
    "Verse-by-verse",
    "Bible view: Strict inerrancy",
    "Charismatic",
    "Deep teaching",
    "Energetic",
    "Member-focused",
    "Worship: Band-led",
    "Long sermons"
  ],
  "swipes": [
    {"pastorName": "MattChandler,", "pastorId": 14, "rating": 4},
    {"pastorName": "JohnPiper",       "pastorId": 4, "rating": 4},
    {"pastorName": "CraigGroeshel",       "pastorId": 1, "rating": 2}
  ]
}

# 1) Validate exact picks
trait_choices = [t.strip() for t in json_from_user["trait_choices"]]
validate_one_per_pair(trait_choices)

# 2) Map to trained trait ids (trait2idx must come from your training artifacts)
# trait2idx = ...  # load from disk (same one used during training)
# For demo, this line will fail if trait2idx isn't defined in your session.
trait_trait_ids = traits_to_trait_ids(trait_choices, trait2idx)


# 3) (Optional) Build preference vector p if model is loaded
# model = ...  # your trained RecSysModelFA
p = build_preference_vector_p(trait_trait_ids, model)
print("p shape:", tuple(p.shape))
print("trait_trait_ids:", trait_trait_ids)

device = next(model.parameters()).device
d = model.user_embed.embedding_dim

# --- 1) Build behavior vector u from swipes (like=4, dislike=2) ---
liked_vs, disliked_vs = [], []
for s in json_from_user["swipes"]:
    item_id = int(s["pastorId"])  
    if item_id not in pastor2idx:
        continue
    idx = pastor2idx[item_id]
    v_id   = model.pastor_id_emb.weight[idx]                     # (d,)
    f_ids  = pastor_trait_ids[idx].to(device)                    # LongTensor of trait ids for this item
    v_feat = model.trait_bag.weight[f_ids].mean(0)              # (d,)
    v = v_id + v_feat
    if float(s["rating"]) >= 4.0:
        liked_vs.append(v)
    else:
        disliked_vs.append(v)

v_like = torch.stack(liked_vs, dim=0).mean(0) if liked_vs else torch.zeros(d, device=device)
v_dis  = torch.stack(disliked_vs, dim=0).mean(0) if disliked_vs else torch.zeros(d, device=device)
u = v_like - 0.5 * v_dis                                        # (d,)

# --- 2) Blend with stated preferences p ---
alpha = 0.4
q = (1 - alpha) * u + alpha * p                                 # (d,)

# --- 3) Score all candidates (exclude already-swiped) ---
swiped_idxs = {pastor2idx[int(s["pastorId"])] for s in json_from_user["swipes"] if int(s["pastorId"]) in pastor2idx}
cand_idxs = [idx for _, idx in pastor2idx.items() if idx not in swiped_idxs]

cand_idx_t = torch.tensor(cand_idxs, dtype=torch.long, device=device)

# Build one big bag for all candidates (like your collate)
flat, offsets, total = [], [0], 0
for i in cand_idxs:
    f = pastor_trait_ids[i].tolist()
    flat.extend(f); total += len(f); offsets.append(total)
flat_t    = torch.tensor(flat, dtype=torch.long, device=device)
offsets_t = torch.tensor(offsets[:-1], dtype=torch.long, device=device)

# Item vectors
v_id   = model.pastor_id_emb(cand_idx_t)                         # (N, d)
v_feat = model.trait_bag(flat_t, offsets_t)                     # (N, d)
V = v_id + v_feat                                               # (N, d)

# Scores (no user_bias for a temp user; that’s fine)
dot  = (V * q.unsqueeze(0)).sum(-1) / model._scale              # (N,)
bias = model.global_bias + model.pastor_bias(cand_idx_t).squeeze(-1)
scores = (dot + bias).detach().cpu()

# Top-K (return ids; map to names if you have a lookup)
K = 40
topk_vals, topk_idx = torch.topk(scores, k=min(K, scores.numel()))
idx2itemId = {v: k for k, v in pastor2idx.items()}
top_items = [(int(idx2itemId[cand_idxs[i.item()]]), float(topk_vals[j].item())) for j, i in enumerate(topk_idx)]
print("Top recommendations (itemId, score):", top_items)

def id_and_name_maps(df):
    id_col = 'pastorId' if 'pastorId' in df.columns else 'pastorId'
    name_col = 'pastorName' if 'pastorName' in df.columns else 'title'
    id2name = dict(zip(df[id_col].astype(int), df[name_col].astype(str)))
    return id_col, name_col, id2name

def traits_for_item(df, ext_id):
    id_col = 'pastorId' if 'pastorId' in df.columns else 'pastorId'
    row = df.loc[df[id_col].astype(int) == int(ext_id)]
    if row.empty: 
        return []
    raw = str(row.iloc[0]['traits']) if 'traits' in row.columns else ''
    return [t.strip() for t in raw.split('|') if t.strip()]

idx2trait = {v:k for k,v in trait2idx.items()}
_, _, id2name = id_and_name_maps(pastor_df)
user_traits_set = set(trait_choices)

# 2) Build detailed rows for the top-K
CLAMP = (0.5, 5.0)
results = []
device = next(model.parameters()).device

for ext_id, raw_score in top_items:
    name = id2name.get(int(ext_id), f"Pastor {ext_id}")
    internal_idx = pastor2idx.get(int(ext_id))
    if internal_idx is None:
        continue

    # Item trait vector for alignment
    f_ids = pastor_trait_ids[internal_idx].to(device)
    v_feat = model.trait_bag.weight[f_ids].mean(0)  # same 'mean' bag as training
    content_cosine = F.cosine_similarity(p.unsqueeze(0), v_feat.unsqueeze(0), dim=1).item()

    # Human-readable trait match
    item_traits = traits_for_item(pastor_df, ext_id)
    matched = sorted(user_traits_set.intersection(item_traits))
    unmatched_user = sorted(user_traits_set.difference(item_traits))

    # Optional: top item traits by alignment with p (explains *which* traits pull it up)
    trait_align = []
    for fid in f_ids.tolist():
        token = idx2trait.get(fid, f"fid:{fid}")
        score = float(torch.dot(p, model.trait_bag.weight[fid]).item())
        trait_align.append((token, score))
    trait_align.sort(key=lambda x: x[1], reverse=True)
    top_trait_explanations = [t for t, _ in trait_align[:3]]

    # Display-friendly rating
    pred_rating = min(max(raw_score, CLAMP[0]), CLAMP[1])

    results.append({
        "pastorId": int(ext_id),
        "name": name,
        "rawScore": float(raw_score),
        "predictedRating": float(pred_rating),
        "matchedTraits": matched,
        "unmatchedUserTraits": unmatched_user,
        "contentCosine": float(content_cosine),
        "topItemTraitsByAlignment": top_trait_explanations
    })

# 3) Sort and slice K (you likely already have K; keep it here for safety)
results = sorted(results, key=lambda r: r["rawScore"], reverse=True)[:K]

# Example print
for r in results:
    print(f"{r['name']} (id={r['pastorId']}): score={r['rawScore']:.3f}, "
          f"~rating={r['predictedRating']:.2f}, cosine={r['contentCosine']:.3f}")
    print("  matches:", ", ".join(r["matchedTraits"]) or "—")
    print("  top item traits by alignment:", ", ".join(r["topItemTraitsByAlignment"]))
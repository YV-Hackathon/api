import pandas as pd
from pathlib import Path
from utils.model import build_mappings
from utils.save_or_load import load_artifacts
import torch.nn.functional as F
import re, unicodedata

# model_path = Path("artifacts","model_1759812063")
# model_path = Path("artifacts","model_1759953359")
# model_path = Path("artifacts","model_1759955051")
model_path = Path("artifacts","model_1760050628")

# Load the model and encoders
model, user_enc, pastor_enc, pastor_trait_ids, _, _ = load_artifacts(model_path)

# Load the data to rebuild trait2idx (same as training)
ratings_path = Path("data","user_ratings.csv").resolve()
pastor_path = Path("data","pastor_traits_mapped.csv").resolve()
rating_df = pd.read_csv(ratings_path)
pastor_df = pd.read_csv(pastor_path)

# Rebuild the mappings to get trait2idx
user2idx, pastor2idx, trait2idx, pastor_trait_ids = build_mappings(rating_df, pastor_df)

import torch

# Need to modify the traits in csv retrain the model and start querying again.
# Model request
# model final response with all necessary data
# Remember that we would like to train as we go so this will be hit multiple times potentially.
# "Depth": (
#     "Practical, everyday life application",
#     "Deep, verse-by-verse Scripture teaching",
#     "A balance of both",
# ),
# "Style": (
#     "Warm and conversational",
#     "Calm and reflective",
#     "Passionate and high-energy",
# ),
# "Environment": ("Traditional", "Contemporary", "Blended"),
# "Gender": ("Male pastor", "Female pastor", "No preference"),
# "Preaching method": ("Expository", "Topical", "Blend"),
# "Theological tradition": ("Reformed/Calvinist", "Arminian/Wesleyan", "Mixed"),
# "Charismatic stance": ("Continuationist", "Cessationist", "Open-but-cautious"),
# "Liturgy formality": ("High-church", "Mid-liturgical", "Low-church"),
# "Sermon length band": ("Short (<25m)", "Medium (25–40m)", "Long (>40m)"),
# "Invitation style": ("Weekly altar call", "Occasional", "Rare/none"),
# "Communion frequency": ("Weekly", "Monthly/Quarterly", "Occasional"),
# "Church polity": (
#     "Episcopal (bishops)",
#     "Presbyterian (elders)",
#     "Congregational (local autonomy)",
# ),
# "Women in leadership": ("Egalitarian", "Complementarian", "Mixed/transitioning"),
# "Size & structure": ("Small (<200)", "Mid (200–1000)", "Mega/Multisite (2000+)"),
# "Discipleship model": ("Small-groups centric", "Classes/courses", "From-the-pulpit"),
# "Newcomer strategy": ("Seeker-sensitive", "Church-family-oriented", "Hybrid"),
# "Worship participation": ("Call-and-response", "Steady monologue", "Contemplative"),


CANONICAL_TRIPLES = {
    (
        "Depth::Practical, everyday life application",
        "Depth::Deep, verse-by-verse Scripture teaching",
        "Depth::A balance of both",
    ),
    (
        "Style::Warm and conversational",
        "Style::Calm and reflective",
        "Style::Passionate and high-energy",
    ),
    ("Environment::Traditional", "Environment::Contemporary", "Environment::Blended"),
    ("Gender::Male pastor", "Gender::Female pastor", "Gender::No preference"),
    ("Preaching method::Expository", "Preaching method::Topical", "Preaching method::Blend"),
    ("Theological tradition::Reformed/Calvinist", "Theological tradition::Arminian/Wesleyan", "Theological tradition::Mixed"),
    ("Charismatic stance::Continuationist", "Charismatic stance::Cessationist", "Charismatic stance::Open-but-cautious"),
    ("Liturgy formality::High-church", "Liturgy formality::Mid-liturgical", "Liturgy formality::Low-church"),
    ("Sermon length band::Short (<25m)", "Sermon length band::Medium (25–40m)", "Sermon length band::Long (>40m)"),
    ("Communion frequency::Weekly altar call", "Communion frequency::Occasional", "Communion frequency::Rare/none"),
    ("Communion frequency::Weekly", "Communion frequency::Monthly/Quarterly", "Communion frequency::Occasional"),
    (
        "Church polity::Episcopal (bishops)",
        "Church polity::Presbyterian (elders)",
        "Church polity::Congregational (local autonomy)",
    ),
    ("Women in leadership::Egalitarian", "Women in leadership::Complementarian", "Women in leadership::Mixed/transitioning"),
    ("Size & structure::Small (<200)", "Size & structure::Mid (200–1000)", "Size & structure::Mega/Multisite (2000+)"),
    ("Discipleship model::Small-groups centric", "Discipleship model::Classes/courses", "Discipleship model::From-the-pulpit"),
    ("Newcomer strategy::Seeker-sensitive", "Newcomer strategy::Church-family-oriented", "Newcomer strategy::Hybrid"),
    ("Worship participation::Call-and-response", "Worship participation::Steady monologue", "Worship participation::Contemplative"),
}


def _strip_group_prefix(token: str) -> str:
    """Return the part after '::' if present, otherwise the original token."""
    return token.split("::", 1)[-1]

# Same triples but with everything before '::' stripped off in each token
CANONICAL_TRIPLES_STRIPPED = tuple(
    tuple(_strip_group_prefix(t) for t in triple) for triple in CANONICAL_TRIPLES
)


def normalize(s: str) -> str:
    s = unicodedata.normalize('NFKC', s)
    s = s.replace('\u2013', '-').replace('\u2014', '-')  # en/em dash -> hyphen
    s = s.replace('\n', ' ').replace('\r', ' ')
    s = re.sub(r'\s+', ' ', s).strip()
    return s
    
# All valid trait VALUES (without group prefix) for simple membership checks
TRAIT_LIST = {normalize(t) for triple in CANONICAL_TRIPLES_STRIPPED for t in triple}


def validate_one_per_pair(traits: list[str]) -> None:
    # Compare values-only (strip group prefix if present) against the allowed list
    values_only = {normalize(t.split("::", 1)[-1]) for t in traits}
    if not values_only.issubset(TRAIT_LIST):
        bad = sorted(values_only.difference(TRAIT_LIST))
        raise ValueError(f"Unknown trait value(s): {bad}")
    # Optionally: enforce exactly one per group if needed


def traits_to_trait_ids(values: list[str], trait2idx: dict[str, int]) -> list[int]:
    """Resolve trait selections to trained IDs when the model was trained on value-only tokens.

    - Accepts inputs like "Group::Value" or just "Value".
    - Always looks up by the Value portion against trait2idx keys.
    - Performs lenient matching (ignoring commas) when exact value isn't found.
    """
    def norm(s: str) -> str:
        return ' '.join(str(s).replace('–', '-').split()).strip()

    def loose_norm(s: str) -> str:
        return norm(s).replace(',', '')

    # Build maps from value-only -> token key present in trait2idx
    exact_value_to_key: dict[str, str] = {}
    loose_value_to_keys: dict[str, list[str]] = {}

    for tok in trait2idx.keys():
        # Extract value portion if keys happen to be in Group::Value form; otherwise use tok as-is
        value_part = tok.split('::', 1)[-1]
        v_exact = norm(value_part)
        v_loose = loose_norm(value_part)
        exact_value_to_key.setdefault(v_exact, tok)
        loose_value_to_keys.setdefault(v_loose, []).append(tok)

    resolved_keys: list[str] = []
    for raw in values:
        # Always resolve by value (strip any group prefix if provided)
        value_only = raw.split('::', 1)[-1]
        v_exact = norm(value_only)
        v_loose = loose_norm(value_only)

        key = exact_value_to_key.get(v_exact)
        if key is None:
            candidates = loose_value_to_keys.get(v_loose, [])
            if not candidates:
                raise KeyError(f"Unknown trait value: {raw}")
            # If multiple candidates share the same value across groups, pick the first
            # (training on value-only implies they are equivalent for embedding lookup)
            key = candidates[0]
        resolved_keys.append(key)

    return [trait2idx[k] for k in resolved_keys]

def build_preference_vector_p(trait_ids: list[int], model, device=None) -> torch.Tensor:
    if device is None:
        device = next(model.parameters()).device
    idx = torch.tensor(trait_ids, dtype=torch.long, device=device)
    # Mean of selected trait embeddings (same as your EmbeddingBag 'mean')
    emb = model.trait_bag.weight.index_select(0, idx)  # (n_traits, d)
    return emb.mean(dim=0)  # (d,)

def id_and_name_maps(df):
    df = df.head(39)
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

# ----- Use with your JSON -----

json_from_user = {
  "trait_choices": [
    "Gender::Female pastor",
    "Preaching method::Topical",
    "Theological tradition::Mixed",
    "Women in leadership::Egalitarian",
  ],
  "swipes": [
    {"pastorName": "AndyStanley,", "pastorId": 44, "rating": 5},
    {"pastorName": "RickWarren",       "pastorId": 45, "rating": 4},
    {"pastorName": "JohnPiper",       "pastorId": 48, "rating": 2}
  ]
}


def get_reccomendations():
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

    # c

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

        # Return church address and name
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

    return results
    # Think about how to store this in the database
    # user id
    # list of recommendations

get_reccomendations()
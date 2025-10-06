import pandas as pd
from sklearn import preprocessing, model_selection
import torch
import math
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from pathlib import Path
from functools import partial
from typing import Tuple

EPOCHS = 40
SEED = 42


DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

ratings_path = Path("data","pastor_ratings.csv").resolve()
pastor_path = Path("data","pastor_traits.csv").resolve()

rating_df = pd.read_csv(ratings_path)
pastor_df = pd.read_csv(pastor_path)


class PastorDataSet(Dataset):
    """
    Class to handle pastor recomendation data
    """
    def __init__(self, df, user2idx, pastor2idx):
        u = df['userId'].map(user2idx).fillna(len(user2idx)).astype('int64')
        m = df['pastorId'].map(pastor2idx).fillna(len(pastor2idx)).astype('int64')
        self.users   = u.to_numpy()
        self.pastors  = m.to_numpy()
        self.ratings = df['rating'].astype('float32').to_numpy()

    def __len__(self):
      return len(self.users)

    def __getitem__(self, i):
        return int(self.users[i]), int(self.pastors[i]), float(self.ratings[i])


class RecSysModelFA(nn.Module):
    """
    Neural network for pastor prediction using collaborative filtering via augmented matrix factorization

    """
    def __init__(self, n_user, n_pastors, n_traits, d=32, bag_mode='mean'):
        super().__init__()
        # ID embeddings (same as your current model)
        self.user_embed   = nn.Embedding(n_user,   d)
        self.pastor_id_emb = nn.Embedding(n_pastors, d)

        # NEW: trait "W f_i" term implemented as a bag of trait embeddings
        self.trait_bag    = nn.EmbeddingBag(n_traits, d, mode=bag_mode)

        # Bias terms + global offset
        self.user_bias   = nn.Embedding(n_user, 1)
        self.pastor_bias  = nn.Embedding(n_pastors, 1)
        self.global_bias = nn.Parameter(torch.zeros(1))

        # small, stable init
        for emb in (self.user_embed, self.pastor_id_emb, self.trait_bag):
            nn.init.normal_(emb.weight, mean=0.0, std=0.05)
        nn.init.zeros_(self.user_bias.weight)
        nn.init.zeros_(self.pastor_bias.weight)

        self._scale = math.sqrt(d)

    def forward(self, users, pastors, trait_idx, trait_offsets):
        """
        Predicts a user's rating for a pastor by combining their learned preferences with the pastor's personality and traits

        Formula:
        Predicted Rating = (User × Pastor) + User Bias + Pastor Bias + Global Bias

        """
        u = self.user_embed(users)                  # (B, d)
        v_id = self.pastor_id_emb(pastors)            # (B, d)
        v_feat = self.trait_bag(trait_idx, trait_offsets)  # (B, d) = W f_i
        v = v_id + v_feat                           # V_i = V_id + W f_i

        dot  = (u * v).sum(-1) / self._scale        # (B,)
        bias = ( self.global_bias
               + self.user_bias(users).squeeze(-1)
               + self.pastor_bias(pastors).squeeze(-1) )
        return dot + bias

def collate_with_traits(batch, pastor_trait_ids):
    """
    Takes in batch of pastor rating data and prepares it for the neural network
    """
    users, pastors, ratings = zip(*batch)
    users   = torch.tensor(users,   dtype=torch.long)
    pastors  = torch.tensor(pastors,  dtype=torch.long)
    ratings = torch.tensor(ratings, dtype=torch.float32)

    # Build flattened trait index list + offsets (one "bag" per pastor)
    flat, offsets = [], [0]
    for pastorIdx in pastors.tolist():
        trait_ids = pastor_trait_ids[pastorIdx]
        flat.extend(trait_ids.tolist())
        offsets.append(offsets[-1] + len(trait_ids))
    trait_idx     = torch.tensor(flat,           dtype=torch.long)
    trait_offsets = torch.tensor(offsets[:-1],   dtype=torch.long)  # length = batch size

    return {"users": users, "pastors": pastors, "ratings": ratings,
            "trait_idx": trait_idx, "trait_offsets": trait_offsets}

def build_mappings(ratings_df : pd.DataFrame , pastors_df : pd.DataFrame):
    """
    Creates look up tables by converting real Ids and traits into numbers the model can understand
    """
    # Map userId/pastorId to contiguous indices for nn.Embedding
    user2idx  = {u:i for i,u in enumerate(sorted(ratings_df['userId'].unique()))}
    pastor2idx = {m:i for i,m in enumerate(sorted(ratings_df['pastorId'].unique()))}


    # All unique traits + a fallback token
    trait_col = pastors_df['traits'].fillna('(no traits listed)')
    all_traits = sorted({g for s in trait_col for g in _parse_traits(s)})
    if '__UNK__' not in all_traits:  # ensure every pastor has ≥1 feature
        all_traits.append('__UNK__')
    trait2idx = {g:i for i,g in enumerate(all_traits)}

    # Per-pastor list of trait ids (by internal pastor index)
    n_pastors = len(pastor2idx)
    pastor_trait_ids = [None]*n_pastors
    for _, row in pastors_df.iterrows():
        if row['pastorId'] in pastor2idx:
            pastor_idx = pastor2idx[row['pastorId']]
            gids = [trait2idx[g] for g in _parse_traits(row['traits'])]
            pastor_trait_ids[pastor_idx] = torch.tensor(gids, dtype=torch.long)

    # Fill any missing/empty with UNK
    unk = trait2idx['__UNK__']
    for i in range(n_pastors):
        if pastor_trait_ids[i] is None or len(pastor_trait_ids[i]) == 0:
            pastor_trait_ids[i] = torch.tensor([unk], dtype=torch.long)

    return user2idx, pastor2idx, trait2idx, pastor_trait_ids

def _parse_traits(s:str) -> list[str]:
    """
        Splits up pastor traits that are stored as a single string into individual trait names.
    """
    if pd.isna(s) or s == '' or s == '(no traits listed)':
        return ['__UNK__']
    return s.split('|')

def run_epoch(model, loss_func, optimizer, loader, device, train: bool, clamp_range=None) -> Tuple[float, float, float]:
    """
    Executes one complete pass of training with all data
    """
    model.train(train)
    total_loss, n = 0.0, 0
    sq_err, abs_err = 0.0, 0.0

    for batch in loader:
        users   = batch["users"].to(device, non_blocking=True)
        pastors  = batch["pastors"].to(device, non_blocking=True)
        ratings = batch["ratings"].to(device, non_blocking=True)
        trait_idx   = batch["trait_idx"].to(device, non_blocking=True)
        trait_offsets   = batch["trait_offsets"].to(device, non_blocking=True)

        # Feature-augmented forward: note the two extra args
        preds = model(users, pastors, trait_idx, trait_offsets)

        # For reporting, optionally clamp to rating range
        preds_for_metrics = preds if clamp_range is None else preds.clamp(*clamp_range)

        loss = loss_func(preds, ratings)
        if train:
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()

        bs = ratings.size(0)
        total_loss += loss.item() * bs
        n += bs

        diff = (preds_for_metrics.detach() - ratings.detach())
        sq_err += torch.sum(diff * diff).item()
        abs_err += torch.sum(diff.abs()).item()

    mse = sq_err / max(n, 1)
    rmse = mse ** 0.5
    mae = abs_err / max(n, 1)
    return total_loss / max(n, 1), rmse, mae

def _build_seen(train_df):
    d = {}
    for uid, trait in train_df.groupby('userId'):
        d[int(uid)] = set(int(x) for x in trait['pastorId'].tolist())
    return d

# //modify
def recall_ndcg_at_k(model, user2idx, pastor2idx, pastor_trait_ids, df_train, df_holdout, device, k=10):
    if df_holdout.empty:
        return float('nan'), float('nan')
    cand_raw = sorted(df_train['pastorId'].unique().tolist())
    cand_idx = torch.tensor([pastor2idx[m] for m in cand_raw], dtype=torch.long, device=device)
    flat, offsets, t = [], [0], 0
    for m in cand_raw:
        gids = pastor_trait_ids[pastor2idx[m]].tolist()
        flat.extend(gids)
        t += len(gids)
        offsets.append(t)
    trait_idx = torch.tensor(flat, dtype=torch.long, device=device)
    trait_off = torch.tensor(offsets[:-1], dtype=torch.long, device=device)
    seen = _build_seen(df_train)
    recs, ndcgs = [], []
    model.eval()
    with torch.no_grad():
        for uid, g in df_holdout.groupby('userId'):
            rel = set(int(x) for x in g['pastorId'].tolist()) & set(cand_raw)
            if not rel:
                continue
            mask = torch.tensor([0 if m in seen.get(int(uid), set()) else 1 for m in cand_raw], dtype=torch.bool, device=device)
            u = torch.tensor([user2idx.get(int(uid), len(user2idx))], dtype=torch.long, device=device).expand(cand_idx.size(0))
            scores = model(u, cand_idx, trait_idx, trait_off)
            scores = torch.where(mask, scores, torch.tensor(-1e9, device=device))
            top = torch.topk(scores, k=min(k, scores.numel()))
            top_ids = [cand_raw[i] for i in top.indices.detach().cpu().tolist()]
            hits = sum(1 for m in rel if m in top_ids)
            denom = min(len(rel), k)
            recs.append(hits/denom if denom>0 else 0.0)
            dcg = 0.0
            for r, mid in enumerate(top_ids, start=1):
                if mid in rel:
                    dcg += 1.0 / math.log2(r + 1)
            ideal = sum(1.0 / math.log2(i + 2) for i in range(min(len(rel), k)))
            ndcgs.append(dcg/ideal if ideal>0 else 0.0)
    if not recs:
        return float('nan'), float('nan')
    return float(sum(recs)/len(recs)), float(sum(ndcgs)/len(ndcgs))
# modify
def recall_ndcg_at_k_sampled(model, user2idx, pastor2idx, pastor_trait_ids,
                             df_train, df_holdout, all_pastors, device,
                             k=10, negatives_per_user=99, seed=42):
    if df_holdout.empty:
        return float('nan'), float('nan')
    rng = torch.Generator(device=device).manual_seed(seed)
    seen = {}
    for uid, g in df_train.groupby('userId'):
        seen[int(uid)] = set(int(x) for x in g['pastorId'].tolist())
    all_pastors = [int(m) for m in all_pastors]

    recs, ndcgs = [], []
    model.eval()
    with torch.no_grad():
        for uid, g in df_holdout.groupby('userId'):
            uid = int(uid)
            rel_items = [int(x) for x in g['pastorId'].tolist()
                         if int(x) in pastor2idx and int(x) not in seen.get(uid, set())]
            if not rel_items:
                continue
            neg_pool = [m for m in all_pastors if m not in seen.get(uid, set()) and m not in rel_items and m in pastor2idx]
            if len(neg_pool) == 0:
                continue
            idx = torch.randint(high=len(neg_pool), size=(min(negatives_per_user, len(neg_pool)),), generator=rng, device=device)
            negs = [neg_pool[i.item()] for i in idx]
            cand = rel_items + negs

            c_idx = torch.tensor([pastor2idx[m] for m in cand], dtype=torch.long, device=device)
            flat, offsets, t = [], [0], 0
            for m in cand:
                gids = pastor_trait_ids[pastor2idx[m]].tolist()
                flat.extend(gids); t += len(gids); offsets.append(t)
            g_idx = torch.tensor(flat, dtype=torch.long, device=device)
            g_off = torch.tensor(offsets[:-1], dtype=torch.long, device=device)

            u = torch.tensor([user2idx.get(uid, len(user2idx))], dtype=torch.long, device=device).expand(c_idx.size(0))
            scores = model(u, c_idx, g_idx, g_off)
            top = torch.topk(scores, k=min(k, scores.numel()))
            top_ids = [cand[i] for i in top.indices.detach().cpu().tolist()]

            hits = sum(1 for m in rel_items if m in top_ids)
            denom = min(len(rel_items), k)
            recs.append(hits/denom if denom > 0 else 0.0)

            dcg = 0.0
            for r, mid in enumerate(top_ids, start=1):
                if mid in rel_items:
                    dcg += 1.0 / math.log2(r + 1)
            ideal = sum(1.0 / math.log2(i + 2) for i in range(min(len(rel_items), k)))
            ndcgs.append(dcg/ideal if ideal > 0 else 0.0)

    if not recs:
        return float('nan'), float('nan')
    return float(sum(recs)/len(recs)), float(sum(ndcgs)/len(ndcgs))

rating_df.info()

rating_df.rating.value_counts()

rating_df.shape

user_enc = preprocessing.LabelEncoder()
pastor_enc = preprocessing.LabelEncoder()
rating_df["userId"]  = user_enc.fit_transform(rating_df["userId"])
rating_df["pastorId"] = pastor_enc.fit_transform(rating_df["pastorId"])

torch.manual_seed(SEED)
torch.cuda.manual_seed_all(SEED)

df_temp, df_test = model_selection.train_test_split(
    rating_df[["userId", "pastorId", "rating"]],
    test_size=0.2,
    random_state=SEED,
)
# Split the dataframe into training and validation sets
df_train, df_valid = model_selection.train_test_split(
    df_temp,
    test_size=0.1,
    random_state=SEED,
)


user2idx, pastor2idx, trait2idx, pastor_trait_ids = build_mappings(
ratings_df=df_train,      # or use the union if you prefer fixed indexing
pastors_df=pastor_df
)

unk_trait = trait2idx['__UNK__']
pastor_trait_ids.append(torch.tensor([unk_trait], dtype=torch.long))

train_dataset = PastorDataSet(
    df_train,
    user2idx,
    pastor2idx
)
valid_dataset = PastorDataSet(
    df_valid,
    user2idx,
    pastor2idx
)
test_dataset = PastorDataSet(
    df_test,
    user2idx,
    pastor2idx
)


# 4) Sizes for the model
n_users  = rating_df.userId.nunique()
n_pastors = rating_df.pastorId.nunique()

collate = partial(collate_with_traits, pastor_trait_ids=pastor_trait_ids)

nw = 4 if DEVICE.type == "cuda" else 0
pin = DEVICE.type == "cuda"
train_loader = DataLoader(train_dataset,  batch_size=2048, shuffle=True,  collate_fn=collate, num_workers=nw, pin_memory=pin, persistent_workers=nw>0)
valid_loader = DataLoader(valid_dataset,  batch_size=4096, shuffle=False, collate_fn=collate, num_workers=nw, pin_memory=pin, persistent_workers=nw>0)
test_loader  = DataLoader(test_dataset,   batch_size=4096, shuffle=False, collate_fn=collate, num_workers=nw, pin_memory=pin, persistent_workers=nw>0)

model = RecSysModelFA(
    n_user=len(user2idx) + 1,
    n_pastors=len(pastor2idx) + 1,
    n_traits=len(trait2idx)
).to(DEVICE)

# Set global bias to mean training rating
with torch.no_grad():
    model.global_bias.fill_(float(df_train["rating"].mean()))
wd = 1e-4
optimizer = torch.optim.AdamW([
    {"params": model.user_embed.parameters(),   "weight_decay": wd},
    {"params": model.pastor_id_emb.parameters(), "weight_decay": wd},
    {"params": model.trait_bag.parameters(),    "weight_decay": wd * 2.0},
    {"params": model.user_bias.parameters(),    "weight_decay": 0.0},
    {"params": model.pastor_bias.parameters(),   "weight_decay": 0.0},
    {"params": [model.global_bias],             "weight_decay": 0.0},
], lr=1e-3)

sched = torch.optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.5)
best = float("inf"); patience=5; bad=0

loss_func = nn.SmoothL1Loss(beta=1.0)

for epoch in range(1, EPOCHS):
    CLAMP = (0.5, 5.0)
    train_loss, train_rmse, train_mae = run_epoch(model, loss_func, optimizer, train_loader, DEVICE, train=True,  clamp_range=CLAMP)
    val_loss,   val_rmse,   val_mae   = run_epoch(model, loss_func, optimizer, valid_loader, DEVICE, train=False, clamp_range=CLAMP)

    sched.step(val_loss)

    print(f"Epoch {epoch:02d} | "
        f"train: loss {train_loss:.4f}, RMSE {train_rmse:.4f}, MAE {train_mae:.4f} | "
        f"valid: loss {val_loss:.4f}, RMSE {val_rmse:.4f}, MAE {val_mae:.4f}")

    if val_loss < best - 1e-4: best = val_loss; bad = 0
    else: bad += 1
    if bad >= patience: break

# Final evaluation on unseen test data
test_loss, test_rmse, test_mae = run_epoch(model, loss_func, optimizer, test_loader, DEVICE, train=False)
print(f"Final Test Performance: Loss {test_loss:.4f}, RMSE {test_rmse:.4f}, MAE {test_mae:.4f}")

# # % of val/test rows that are NEW (unseen in train)
# val_new_users  = (~df_valid['userId'].isin(df_train['userId'])).mean()
# val_new_pastors = (~df_valid['pastorId'].isin(df_train['pastorId'])).mean()
# test_new_users  = (~df_test['userId'].isin(df_train['userId'])).mean()
# test_new_pastors = (~df_test['pastorId'].isin(df_train['pastorId'])).mean()
# print(val_new_users, val_new_pastors, test_new_users, test_new_pastors)

# # Baseline sanity check: global-mean predictor RMSE
# mean_rating = df_train['rating'].mean()
# val_rmse_baseline  = (((df_valid['rating'] - mean_rating)**2).mean()) ** 0.5
# test_rmse_baseline = (((df_test['rating']  - mean_rating)**2).mean()) ** 0.5
# print(val_rmse_baseline, test_rmse_baseline)


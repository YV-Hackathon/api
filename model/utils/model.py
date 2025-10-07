import torch
import pandas as pd
import math
from typing import Tuple

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

from pathlib import Path

import pandas as pd
from sklearn import preprocessing, model_selection

import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from functools import partial

from classes import PastorDataSet, RecSysModelFA

from utils.model import collate_with_traits,build_mappings,run_epoch
from utils.save_or_load import save_artifacts

EPOCHS = 40
SEED = 42


DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

ratings_path = Path("data","pastor_ratings.csv").resolve()
pastor_path = Path("data","pastor_traits.csv").resolve()

rating_df = pd.read_csv(ratings_path)
pastor_df = pd.read_csv(pastor_path)


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

save_artifacts(
    model,
    len(user2idx) + 1,
    len(pastor2idx) + 1,
    len(trait2idx),
    32,
    user_enc,
    pastor_enc,
    pastor_trait_ids
)

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


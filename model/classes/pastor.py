import torch
import math

from torch.utils.data import Dataset
import torch.nn as nn

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

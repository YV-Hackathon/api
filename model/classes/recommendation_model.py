import torch
import math

import torch.nn as nn

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

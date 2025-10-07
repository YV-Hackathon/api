from pathlib import Path
import time
import torch
import joblib

from classes import RecSysModelFA

def save_artifacts(
    model,
    n_users: int,
    n_pastors: int,
    n_traits: int,
    d: int,
    user_enc,
    pastor_enc,
    pastor_trait_ids,
    optimizer=None,
    scheduler=None,
    rating_min: float = None,
    rating_max: float = None,
) -> Path:
    stamp = str(int(time.time()))
    out_dir = Path("artifacts",f"model_{stamp}").resolve()
    out_dir.mkdir(parents=True, exist_ok=True, )

    # 1) Model checkpoint
    ckpt_path = out_dir / "checkpoint.pt"
    torch.save({
        "model_state_dict": model.state_dict(),
        "n_users": n_users,
        "n_pastors": n_pastors,
        "n_traits": n_traits,
        "d": d,
        "rating_min": rating_min,
        "rating_max": rating_max,
    }, ckpt_path)

    # 2) Optimizer / scheduler (optional)
    if optimizer is not None:
        torch.save({"optimizer_state_dict": optimizer.state_dict()}, out_dir / "optimizer.pt")
    if scheduler is not None:
        torch.save({"scheduler_state_dict": scheduler.state_dict()}, out_dir / "scheduler.pt")

    # 3) Encoders and trait mappings
    joblib.dump(user_enc,  out_dir / "user_encoder.pkl")
    joblib.dump(pastor_enc, out_dir / "pastor_encoder.pkl")
    joblib.dump(pastor_trait_ids, out_dir / "pastor_trait_ids.pkl")

    print(f"Saved artifacts to: {out_dir}")
    return out_dir

def load_artifacts(ckpt_dir: Path):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    ckpt_dir = ckpt_dir.resolve()
    ckpt = torch.load(ckpt_dir / "checkpoint.pt", map_location=device, weights_only=False)

    # Load encoders first to get correct dimensions
    user_enc  = joblib.load(ckpt_dir / "user_encoder.pkl")
    pastor_enc = joblib.load(ckpt_dir / "pastor_encoder.pkl")
    
    # Debug: Check what's in the checkpoint
    print("Checkpoint keys:", list(ckpt.keys()))
    print("n_users:", ckpt.get("n_users"))
    print("n_pastors:", ckpt.get("n_pastors")) 
    print("n_traits:", ckpt.get("n_traits"))
    print("d:", ckpt.get("d"))
    
    model = RecSysModelFA(
        n_user=ckpt["n_users"],
        n_pastors=ckpt["n_pastors"],
        n_traits=ckpt["n_traits"],
        d=ckpt["d"],
    ).to(device)

    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()

    user_enc  = joblib.load(ckpt_dir / "user_encoder.pkl")
    pastor_enc = joblib.load(ckpt_dir / "pastor_encoder.pkl")
    pastor_trait_ids = joblib.load(ckpt_dir / "pastor_trait_ids.pkl")

    R_MIN = ckpt.get("rating_min", None)
    R_MAX = ckpt.get("rating_max", None)

    return model, user_enc, pastor_enc, pastor_trait_ids, R_MIN, R_MAX
from logging import warning
import os
import pandas as pd
import random
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PATH = os.path.join(BASE_DIR, "data", "processed", "dataset.csv")


# -----------------------------
# Sigmoid function (UNCHANGED)
# -----------------------------
def sigmoid(x):
    return 1 / (1 + np.exp(-x))


# -----------------------------
# ✅ FIXED LABEL FUNCTION (SAFE)
# -----------------------------
def generate_label(error, warning, dependency, install_steps):
    # 🔧 Reduce dominance of error/warning
    error_score      = (error   / 6.0) * 2.0   # was 3.0
    warning_score    = (warning / 8.0) * 1.2   # was 1.5
    dep_score        = (dependency / 60.0) * 0.8
    install_score    = (install_steps - 1) * 0.4

    raw = error_score + warning_score + dep_score + install_score - 2.0  # was -2.2
    # strengthen extremes
    if error >= 6:
        raw += 0.6
    if warning >= 8:
        raw += 0.6

    prob = sigmoid(raw)

    # 🔧 Reduce noise slightly
    noise = random.uniform(-0.03, 0.03)
    prob  = min(1.0, max(0.0, prob + noise))

    # 🔥 KEY FIX: uncertainty zone (prevents binary jump)
    if prob > 0.65:
        return 1
    elif prob < 0.35:
        return 0
    else:
        return random.choice([0, 1])

# -----------------------------
# Sample generation (MINOR TUNE ONLY)
# -----------------------------
def generate_sample():
    # Slightly improved distribution (still compatible)
    error_count = int(np.clip(abs(np.random.normal(loc=2.0, scale=1.8)), 0, 8))
    warning_count = int(np.clip(abs(np.random.normal(loc=3.5, scale=2.5)), 0, 10))
    if error_count >= 6:
        warning_count = min(10, warning_count + random.choice([1, 2]))

    # Light noise (UNCHANGED logic)
    error_count   = max(0, error_count   + random.choice([-1, 0, 0, 1]))
    warning_count = max(0, warning_count + random.choice([-1, 0, 0, 1]))

    dependency_downloads = int(np.clip(
        abs(np.random.normal(loc=20 + error_count * 2, scale=12)),
        5, 70
    ))

    install_steps = random.choices([1, 2, 3], weights=[0.6, 0.3, 0.1])[0]
    has_git_clone = 1

    return {
        "error_count":          error_count,
        "warning_count":        warning_count,
        "dependency_downloads": dependency_downloads,
        "install_steps":        install_steps,
        "has_git_clone":        has_git_clone,
    }


# -----------------------------
# Dataset generation (UNCHANGED)
# -----------------------------
def generate_dataset(size=5000):
    data = []
    for _ in range(size):
        sample = generate_sample()
        sample["label"] = generate_label(
            sample["error_count"],
            sample["warning_count"],
            sample["dependency_downloads"],
            sample["install_steps"],
        )
        data.append(sample)

    df   = pd.DataFrame(data)
    df_0 = df[df["label"] == 0]
    df_1 = df[df["label"] == 1]
    n    = min(len(df_0), len(df_1))

    df_balanced = pd.concat([
        df_0.sample(n, random_state=42),
        df_1.sample(n, random_state=42)
    ]).sample(frac=1, random_state=42).reset_index(drop=True)

    return df_balanced


# -----------------------------
# MAIN (UNCHANGED)
# -----------------------------
if __name__ == "__main__":
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    df = generate_dataset(size=5000)
    df.to_csv(OUT_PATH, index=False)
    print(f"✅ Dataset saved: {len(df)} records")
    print(f"\nLabel distribution:\n{df['label'].value_counts().to_string()}")
    print(f"\nError count range  : {df['error_count'].min()} – {df['error_count'].max()}")
    print(f"Warning count range: {df['warning_count'].min()} – {df['warning_count'].max()}")
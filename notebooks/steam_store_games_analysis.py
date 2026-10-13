import os
import pandas as pd, numpy as np
import matplotlib.pyplot as plt, seaborn as sns

SHOW_PLOTS = False   # set True to also pop up each chart window
os.makedirs("graphs", exist_ok=True)
sns.set_theme(style="whitegrid")


def save(name):
    plt.tight_layout()
    plt.savefig(f"graphs/{name}.png", dpi=150, bbox_inches="tight")
    if SHOW_PLOTS:
        plt.show()
    plt.close()
    print("saved graphs/" + name + ".png")


# ---------------- Load ----------------
df = pd.read_csv("dataset/steam.csv")
print("Shape:", df.shape)
print(df.head())

# ---------------- Missing values ----------------
print(df.isna().sum()[df.isna().sum() > 0])
df["developer"] = df["developer"].fillna("Unknown")
df["publisher"] = df["publisher"].fillna("Unknown")
print("Nulls left:", df.isna().sum().sum())

# ---------------- Duplicates ----------------
print("Duplicate rows:", df.duplicated().sum())
print("Duplicate appid:", df["appid"].duplicated().sum())
print("Repeated names:", df["name"].duplicated().sum())  # different games, kept
df = df.drop_duplicates().drop_duplicates("appid")
df["name"] = df["name"].str.strip()

# ---------------- Data types ----------------
df["release_date"] = pd.to_datetime(df["release_date"])
df["release_year"] = df["release_date"].dt.year
df["english"] = df["english"].astype(bool)
df["required_age"] = df["required_age"].astype("int8")

rng = df["owners"].str.split("-", expand=True).astype(int)
df["owners_mid"] = (rng[0] + rng[1]) / 2

df["total_ratings"] = df["positive_ratings"] + df["negative_ratings"]
df["positive_pct"] = df["positive_ratings"] / df["total_ratings"].replace(0, np.nan) * 100
df["is_free"] = df["price"] == 0
df["mac"] = df["platforms"].str.contains("mac")
df["linux"] = df["platforms"].str.contains("linux")
print(df.dtypes)

# ---------------- Outliers (IQR) ----------------
for c in ["price", "average_playtime", "positive_ratings", "achievements"]:
    q1, q3 = df[c].quantile([.25, .75])
    hi = q3 + 1.5 * (q3 - q1)
    print(f"{c}: upper limit={hi:.1f}, outliers={(df[c] > hi).sum()}, max={df[c].max()}")

for c in ["price", "average_playtime", "positive_ratings"]:
    df[c + "_capped"] = df[c].clip(upper=df[c].quantile(.99))

paid_all = df[df.price > 0]
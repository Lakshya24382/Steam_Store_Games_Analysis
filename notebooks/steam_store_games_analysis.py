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

# ================= GRAPHS =================

# 1. genre_distribution.png  (bar chart)
plt.figure(figsize=(8, 5))
df["genres"].str.split(";").explode().value_counts().head(10).sort_values().plot(kind="barh", color="navy")
plt.title("Top 10 Genres")
plt.xlabel("Number of games")
save("genre_distribution")

# 2. price_distribution.png  (histogram with KDE)
plt.figure(figsize=(8, 5))
sns.histplot(paid_all["price_capped"], bins=40, kde=True, color="steelblue")
plt.title("Price Distribution (paid games, capped at 99th percentile)")
plt.xlabel("Price (USD)")
save("price_distribution")

# 3. price_outliers.png  (box plot)
plt.figure(figsize=(7, 5))
plt.boxplot([paid_all["price"], paid_all["price_capped"]], tick_labels=["Raw", "Capped"])
plt.title("Price Outliers")
plt.ylabel("Price (USD)")
save("price_outliers")

# 4. games_released_per_year.png  (line chart)
plt.figure(figsize=(9, 5))
per_year = df[df.release_year >= 2006].groupby("release_year").size()
plt.plot(per_year.index, per_year.values, marker="o", color="teal")
plt.title("Games Released per Year (2019 is a partial year)")
plt.xlabel("Release year")
plt.ylabel("Number of games")
save("games_released_per_year")

# 5. free_vs_paid.png  (count plot)
plt.figure(figsize=(6, 5))
labels = df["is_free"].map({True: "Free", False: "Paid"})
ax = sns.countplot(x=labels, order=["Paid", "Free"], hue=labels, palette=["steelblue", "coral"], legend=False)
for p in ax.patches:
    ax.annotate(f"{int(p.get_height()):,}", (p.get_x() + p.get_width() / 2, p.get_height()),
                ha="center", va="bottom")
plt.title("Free vs Paid Games")
plt.xlabel("")
plt.ylabel("Number of games")
save("free_vs_paid")

# 6. price_vs_rating.png  (scatter plot; this dataset has no Metacritic column)
plt.figure(figsize=(8, 5))
rated = paid_all[paid_all.total_ratings >= 50]
corr = rated["price"].corr(rated["positive_pct"], method="spearman")
plt.scatter(rated["price_capped"], rated["positive_pct"], alpha=0.25, s=10, color="teal")
plt.title(f"Price vs Positive Rating % (Spearman r = {corr:.2f})")
plt.xlabel("Price (USD, capped)")
plt.ylabel("Positive rating (%)")
save("price_vs_rating")
print(f"Price vs rating Spearman correlation: {corr:.3f}")

# 7. average_price_by_genre.png  (bar chart)
plt.figure(figsize=(8, 5))
g = paid_all.assign(genre=paid_all["genres"].str.split(";")).explode("genre")
stats = g.groupby("genre")["price"].agg(["mean", "count"])
stats = stats[stats["count"] >= 100]            # ignore tiny genres
stats["mean"].sort_values().tail(10).plot(kind="barh", color="navy")
plt.title("Average Price by Genre (paid games, genres with 100+ games)")
plt.xlabel("Average price (USD)")
save("average_price_by_genre")

# 8. correlation_heatmap.png
plt.figure(figsize=(8, 6))
cols = ["price", "required_age", "achievements", "positive_ratings", "negative_ratings",
        "average_playtime", "owners_mid", "release_year"]
sns.heatmap(df[cols].corr(method="spearman"), annot=True, fmt=".2f", cmap="coolwarm")
plt.title("Spearman Correlation")
save("correlation_heatmap")

# Extra: platform_support.png
plt.figure(figsize=(6, 5))
pd.Series({"Windows": 100, "Mac": df.mac.mean() * 100, "Linux": df.linux.mean() * 100}).plot(
    kind="bar", color=["navy", "teal", "coral"])
plt.title("Platform Support (%)")
plt.ylabel("% of games")
plt.xticks(rotation=0)
save("platform_support")

# ---------------- Summary ----------------
print(f"Games: {len(df):,}")
print(f"Released 2016-2018: {df.release_year.between(2016, 2018).mean() * 100:.1f}%")
print(f"Indie share: {df.genres.str.contains('Indie').mean() * 100:.1f}%")
print(f"Free games: {df.is_free.mean() * 100:.1f}%")
print(f"Median paid price: {df[~df.is_free].price.median()}")
print(f"Games with <=20,000 owners: {(df.owners_mid <= 10000).mean() * 100:.1f}%")
print(f"Median positive rating: {df.positive_pct.median():.1f}%")
print(f"Zero playtime games: {(df.average_playtime == 0).mean() * 100:.1f}%")

# ---------------- Save cleaned data ----------------
df.to_csv("dataset/steam_cleaned.csv", index=False)
print("saved dataset/steam_cleaned.csv")

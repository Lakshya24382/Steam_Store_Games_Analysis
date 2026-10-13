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
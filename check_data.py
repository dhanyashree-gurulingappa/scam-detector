import pandas as pd

df = pd.read_csv("dataset.csv", encoding="utf-8-sig")
print("Total messages:", len(df))
print()
print(df["label"].value_counts())
print()
print(df["language"].value_counts())
print()
print(df.head(8))
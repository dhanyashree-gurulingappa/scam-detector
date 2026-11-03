import os
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import make_pipeline
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from textutils import normalize

df = pd.read_csv("dataset.csv", encoding="utf-8-sig")
df = df.dropna(subset=["text", "label"])
df["label"] = df["label"].str.strip().str.lower()
df["language"] = df["language"].astype(str).str.strip().str.lower()
df["clean"] = df["text"].apply(normalize)
print("Total messages:", len(df))
print(df["label"].value_counts())


def make(clf):
    return make_pipeline(
        TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=2, sublinear_tf=True),
        clf,
    )


def lr():
    return LogisticRegression(max_iter=2000, C=10, class_weight="balanced")


train, test = train_test_split(df, test_size=0.2, stratify=df["label"], random_state=42)

models = {
    "Naive Bayes": MultinomialNB(),
    "Logistic Regression": lr(),
    "Random Forest": RandomForestClassifier(n_estimators=300, random_state=42),
}

for name, clf in models.items():
    pipe = make(clf)
    pipe.fit(train["clean"], train["label"])
    pred = pipe.predict(test["clean"])
    print("\n==========", name, "==========")
    print(classification_report(test["label"], pred))
    print("Confusion matrix:\n", confusion_matrix(test["label"], pred))
    for lang in sorted(test["language"].unique()):
        mask = (test["language"] == lang).values
        if mask.sum() > 0:
            acc = (pred[mask] == test["label"].values[mask]).mean()
            print(f"  {lang}: accuracy {acc:.2f} on {mask.sum()} messages")

print("\n==========  5-fold cross-validation (more reliable)  ==========")
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
for name, clf in [("Naive Bayes", MultinomialNB()), ("Logistic Regression", lr()),
                  ("Random Forest", RandomForestClassifier(n_estimators=300, random_state=42))]:
    scores = cross_val_score(make(clf), df["clean"], df["label"], cv=skf)
    print(f"{name}: {scores.mean()*100:.1f}% (+/- {scores.std()*100:.1f})")

# Final model: train on ALL data for the web app
final = make(lr())
final.fit(df["clean"], df["label"])
joblib.dump(final, "model.joblib")
print("\nSaved model.joblib")

# Honest test on REAL messages (optional): put them in real_test.csv
if os.path.exists("real_test.csv"):
    real = pd.read_csv("real_test.csv", encoding="utf-8-sig").dropna(subset=["text", "label"])
    real["label"] = real["label"].str.strip().str.lower()
    pred = final.predict(real["text"].apply(normalize))
    print("\n==========  REAL MESSAGES TEST  ==========")
    print(classification_report(real["label"], pred))
    print("Confusion matrix:\n", confusion_matrix(real["label"], pred))
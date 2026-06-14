import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
import joblib

# -------------------------
# SAMPLE DATASET (AI LEARNING)
# -------------------------
data = {
    "score": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    "level": [0, 0, 0, 1, 1, 1, 2, 2, 2, 2, 2]
}

# 0 = Weak
# 1 = Average
# 2 = Strong

df = pd.DataFrame(data)

X = df[["score"]]
y = df["level"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

model = LogisticRegression()
model.fit(X_train, y_train)

joblib.dump(model, "model.pkl")

print("Model trained successfully 🚀")
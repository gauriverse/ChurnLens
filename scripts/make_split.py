import pandas as pd

from churnlens.data.splitting import split_data

df = pd.read_csv("data/processed/telco_clean.csv")
X_train, X_test, y_train, y_test = split_data(df)

df.loc[X_train.index].to_csv("data/processed/train.csv", index=False)
df.loc[X_test.index].to_csv("data/processed/test.csv", index=False)

print("train:", len(X_train), "churn rate:", round(y_train.mean(), 3))
print("test: ", len(X_test), "churn rate:", round(y_test.mean(), 3))
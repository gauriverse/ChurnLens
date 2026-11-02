from churnlens.data.cleaning import load_raw, clean_telco

raw = load_raw("data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv")
clean = clean_telco(raw)
clean.to_csv("data/processed/telco_clean.csv", index=False)

print(clean.shape)
print(clean[["TotalCharges", "Churn"]].dtypes)
print("churn rate:", round(clean["Churn"].mean(), 3))
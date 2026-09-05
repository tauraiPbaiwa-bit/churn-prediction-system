"""
Generates a synthetic Telco-style churn dataset for quickly testing the system
end-to-end without needing to source a real dataset first.

Run with: python generate_sample_data.py
Produces: sample_churn_data.csv
"""
import numpy as np
import pandas as pd

np.random.seed(42)
n = 1000

df = pd.DataFrame({
    "customerID": [f"CUST-{i:05d}" for i in range(n)],
    "gender": np.random.choice(["Male", "Female"], n),
    "SeniorCitizen": np.random.choice([0, 1], n, p=[0.85, 0.15]),
    "Partner": np.random.choice(["Yes", "No"], n),
    "Dependents": np.random.choice(["Yes", "No"], n),
    "tenure": np.random.randint(0, 72, n),
    "PhoneService": np.random.choice(["Yes", "No"], n, p=[0.9, 0.1]),
    "MultipleLines": np.random.choice(["Yes", "No", "No phone service"], n),
    "InternetService": np.random.choice(["DSL", "Fiber optic", "No"], n),
    "OnlineSecurity": np.random.choice(["Yes", "No", "No internet service"], n),
    "OnlineBackup": np.random.choice(["Yes", "No", "No internet service"], n),
    "DeviceProtection": np.random.choice(["Yes", "No", "No internet service"], n),
    "TechSupport": np.random.choice(["Yes", "No", "No internet service"], n),
    "StreamingTV": np.random.choice(["Yes", "No", "No internet service"], n),
    "StreamingMovies": np.random.choice(["Yes", "No", "No internet service"], n),
    "Contract": np.random.choice(["Month-to-month", "One year", "Two year"], n, p=[0.55, 0.25, 0.2]),
    "PaperlessBilling": np.random.choice(["Yes", "No"], n),
    "PaymentMethod": np.random.choice(
        ["Electronic check", "Mailed check", "Bank transfer", "Credit card"], n
    ),
    "MonthlyCharges": np.round(np.random.uniform(18, 120, n), 2),
})

df["TotalCharges"] = np.round(df["MonthlyCharges"] * df["tenure"] + np.random.uniform(0, 100, n), 2)

# Make churn probabilistically dependent on tenure/contract to mimic real patterns
churn_prob = (
    0.5
    - 0.006 * df["tenure"]
    + df["Contract"].map({"Month-to-month": 0.25, "One year": 0.0, "Two year": -0.2})
    + df["InternetService"].map({"Fiber optic": 0.1, "DSL": 0.0, "No": -0.15})
).clip(0.02, 0.9)
df["Churn"] = np.where(np.random.rand(n) < churn_prob, "Yes", "No")

# Inject a few missing values & duplicates to exercise the cleaning pipeline
df.loc[np.random.choice(df.index, 15, replace=False), "TotalCharges"] = np.nan
df.loc[np.random.choice(df.index, 8, replace=False), "PaymentMethod"] = None
df = pd.concat([df, df.sample(5, random_state=1)], ignore_index=True)

df.to_csv("sample_churn_data.csv", index=False)
print(f"Generated sample_churn_data.csv with {len(df)} rows (including intentional missing values & duplicates).")

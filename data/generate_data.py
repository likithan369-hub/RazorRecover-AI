import pandas as pd
import numpy as np

np.random.seed(42)

N = 5000

data = pd.DataFrame({
    "transaction_id": [f"TX{i:05d}" for i in range(1, N + 1)],
    "customer_id": [f"CUST{np.random.randint(1, 1500):04d}" for _ in range(N)],
    "amount": np.round(np.random.uniform(200, 50000, N), 2),

    "payment_method": np.random.choice(
        ["UPI", "Card", "NetBanking", "Wallet"], N
    ),

    "transaction_status": np.random.choice(
        ["Success", "Failed", "Abandoned", "Subscription_Failed", "Overdue"],
        N,
        p=[0.55, 0.18, 0.10, 0.10, 0.07]
    ),

    "failure_reason": np.random.choice(
        [
            "Network_Error",
            "Bank_Decline",
            "Insufficient_Funds",
            "Timeout",
            "Authentication_Failed",
            "None"
        ],
        N
    ),

    "retry_count": np.random.randint(0, 4, N),

    "previous_success_rate": np.round(
        np.random.uniform(0.2, 1.0, N), 2
    ),

    "customer_value": np.random.choice(
        ["Low", "Medium", "High"],
        N,
        p=[0.5, 0.35, 0.15]
    ),

    "checkout_duration": np.round(
        np.random.uniform(10, 600, N), 1
    ),

    "days_overdue": np.random.randint(0, 31, N)
})


# -----------------------------------------
# Revenue at risk
# -----------------------------------------

data["revenue_at_risk"] = np.where(
    data["transaction_status"] == "Success",
    0,
    data["amount"]
)


# -----------------------------------------
# Generate realistic recovery probability
# -----------------------------------------

score = (
    data["previous_success_rate"] * 0.45
    + (data["customer_value"] == "High") * 0.20
    + (data["customer_value"] == "Medium") * 0.10
    - data["retry_count"] * 0.08
    - (data["failure_reason"] == "Insufficient_Funds") * 0.20
    - (data["failure_reason"] == "Bank_Decline") * 0.10
    + (data["failure_reason"] == "Network_Error") * 0.10
    + (data["failure_reason"] == "Timeout") * 0.08
)

score = np.clip(score, 0.05, 0.95)


# -----------------------------------------
# Ground truth: eventually recovered?
# -----------------------------------------

data["recovered"] = (
    np.random.random(N) < score
).astype(int)


# Successful transactions are already recovered
data.loc[
    data["transaction_status"] == "Success",
    "recovered"
] = 1


# -----------------------------------------
# Save dataset
# -----------------------------------------

data.to_csv("transactions.csv", index=False)

print("Dataset created successfully!")
print(f"Records: {len(data)}")

print(
    f"Revenue at risk: "
    f"₹{data['revenue_at_risk'].sum():,.2f}"
)

print(
    f"Recovered transactions: "
    f"{data['recovered'].sum()}"
)

print("\nStatus distribution:")
print(data["transaction_status"].value_counts())

print("\nRecovery distribution:")
print(data["recovered"].value_counts())
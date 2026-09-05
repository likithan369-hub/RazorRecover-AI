import pandas as pd

from backend.agent import predict_recovery, choose_intervention
from backend.policies import check_policy

data = pd.read_csv("data/transactions.csv")

blocked = []

for _, row in data.iterrows():

    transaction = row.to_dict()

    if transaction["transaction_status"] == "Success":
        continue

    probability = predict_recovery(transaction)

    action = choose_intervention(
        transaction,
        probability
    )

    allowed, reason = check_policy(
        transaction,
        action
    )

    if not allowed:
        blocked.append({
            "transaction_id": transaction["transaction_id"],
            "status": transaction["transaction_status"],
            "amount": transaction["amount"],
            "retry_count": transaction["retry_count"],
            "probability": probability,
            "action": action,
            "reason": reason
        })

print("\nBLOCKED CASES")
print("=" * 80)

for case in blocked:
    print(case)

print("\nTotal blocked:", len(blocked))
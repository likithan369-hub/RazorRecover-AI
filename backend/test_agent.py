import pandas as pd

from agent import predict_recovery, choose_intervention
from policies import check_policy
from recovery import execute_recovery, create_audit_record


data = pd.read_csv("data/transactions.csv")

transaction = data[
    data["transaction_status"] != "Success"
].iloc[0].to_dict()


# 1. Predict recovery probability
probability = predict_recovery(transaction)


# 2. Choose intervention
recommended_action = choose_intervention(
    transaction,
    probability
)


# 3. Check guardrails
allowed, reason = check_policy(
    transaction,
    recommended_action
)


print("\n===== RAZORRECOVER AI =====")

print(f"Transaction: {transaction['transaction_id']}")
print(f"Amount: ₹{transaction['amount']:,.2f}")
print(f"Status: {transaction['transaction_status']}")

print(
    f"\nRecovery probability: "
    f"{probability * 100:.2f}%"
)

print(f"AI recommendation: {recommended_action}")


# 4. Execute only if policy allows
if allowed:

    result = execute_recovery(
        transaction,
        recommended_action
    )

else:

    result = {
        "status": "BLOCKED",
        "message": reason,
        "recovered_amount": 0
    }


# 5. Create audit record
audit = create_audit_record(
    transaction,
    probability,
    recommended_action,
    result
)


print("\n===== GUARDRAIL =====")
print(
    "ALLOWED" if allowed else "BLOCKED"
)
print(reason)


print("\n===== EXECUTION =====")
print(f"Status: {result['status']}")
print(f"Message: {result['message']}")
print(
    f"Recovered: ₹{result['recovered_amount']:,.2f}"
)


print("\n===== AUDIT TRAIL =====")

for key, value in audit.items():
    print(f"{key}: {value}")
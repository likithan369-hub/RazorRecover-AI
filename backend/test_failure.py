import pandas as pd

from failure_handler import handle_payment_failure


data = pd.read_csv("data/transactions.csv")

transaction = data[
    data["transaction_status"] == "Failed"
].iloc[0].to_dict()


print("\n===== FAILURE HANDLING DEMO =====")

print(f"Transaction: {transaction['transaction_id']}")
print(f"Amount: ₹{transaction['amount']:,.2f}")

print("\nAI Action: RETRY_PAYMENT")
print("Simulated API Failure: TIMEOUT")

result = handle_payment_failure(
    transaction,
    "RETRY_PAYMENT",
    "TIMEOUT"
)

print("\n===== SAFE RECOVERY =====")

print(f"Status: {result['status']}")
print(f"Final Action: {result['final_action']}")
print(f"Message: {result['message']}")

print("\n===== AUDIT =====")

for key, value in result.items():
    print(f"{key}: {value}")
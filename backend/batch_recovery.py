import pandas as pd
import os

from agent import predict_recovery, choose_intervention
from policies import check_policy
from recovery import execute_recovery, create_audit_record


# Load dataset
data = pd.read_csv("data/transactions.csv")

audit_records = []

total_revenue_at_risk = 0
total_recovered = 0

successful_recoveries = 0
escalated_cases = 0
blocked_actions = 0
processed_cases = 0


for _, row in data.iterrows():

    transaction = row.to_dict()

    # Ignore already successful transactions
    if transaction["transaction_status"] == "Success":
        continue

    processed_cases += 1

    total_revenue_at_risk += transaction["amount"]

    # 1. Predict recovery probability
    probability = predict_recovery(transaction)

    # 2. Choose intervention
    action = choose_intervention(
        transaction,
        probability
    )

    # 3. Guardrail check
    allowed, reason = check_policy(
        transaction,
        action
    )

    # 4. Execute approved action
    if allowed:

        result = execute_recovery(
            transaction,
            action
        )

    else:

        blocked_actions += 1

        result = {
            "status": "BLOCKED",
            "message": reason,
            "recovered_amount": 0
        }

    # Count outcomes
    if result["status"] == "SUCCESS":
        successful_recoveries += 1

    elif result["status"] == "ESCALATED":
        escalated_cases += 1

    total_recovered += result["recovered_amount"]

    # 5. Audit record
    audit = create_audit_record(
        transaction,
        probability,
        action,
        result
    )

    audit_records.append(audit)


# --------------------------------------------------
# APPEND BATCH AUDIT RECORDS
# --------------------------------------------------

audit_path = "data/audit_trail.csv"

new_audit_df = pd.DataFrame(audit_records)

if not new_audit_df.empty:

    if os.path.exists(audit_path):

        old_audit_df = pd.read_csv(audit_path)

        # Preserve columns from both files
        for column in new_audit_df.columns:
            if column not in old_audit_df.columns:
                old_audit_df[column] = ""

        for column in old_audit_df.columns:
            if column not in new_audit_df.columns:
                new_audit_df[column] = ""

        # Keep existing column order
        new_audit_df = new_audit_df[old_audit_df.columns]

        # Append instead of overwrite
        audit_df = pd.concat(
            [old_audit_df, new_audit_df],
            ignore_index=True
        )

    else:
        audit_df = new_audit_df

    audit_df.to_csv(
        audit_path,
        index=False
    )

    print("\n✅ Batch audit records appended successfully.")

else:

    print("\n⚠️ No batch audit records generated.")


# Calculate recovery rate
recovery_rate = (
    total_recovered / total_revenue_at_risk * 100
    if total_revenue_at_risk > 0
    else 0
)


print("\n")
print("=" * 60)
print("           RAZORRECOVER AI - BATCH RESULTS")
print("=" * 60)

print(f"\nTransactions processed : {processed_cases}")

print(
    f"Revenue at risk        : "
    f"₹{total_revenue_at_risk:,.2f}"
)

print(
    f"Revenue recovered      : "
    f"₹{total_recovered:,.2f}"
)

print(
    f"Recovery rate          : "
    f"{recovery_rate:.2f}%"
)

print(
    f"Successful recoveries  : "
    f"{successful_recoveries}"
)

print(
    f"Escalated cases        : "
    f"{escalated_cases}"
)

print(
    f"Blocked actions        : "
    f"{blocked_actions}"
)

print("\nAudit trail saved to:")
print("data/audit_trail.csv")

print("=" * 60)
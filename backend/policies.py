def check_policy(transaction, action):
    """
    Validate whether the AI-recommended action
    is allowed by our financial safety policies.
    """

    retry_count = transaction["retry_count"]
    amount = transaction["amount"]

    # Rule 1: Never allow more than 2 retries
    if action == "RETRY_PAYMENT" and retry_count >= 2:
        return False, "Maximum retry limit reached"

    # Rule 2: High-value transactions require escalation
    if action == "RETRY_PAYMENT" and amount >= 30000:
        return False, "High-value transaction requires escalation"

    # Rule 3: Never automatically retry overdue transactions
    if action == "RETRY_PAYMENT" and transaction["transaction_status"] == "Overdue":
        return False, "Overdue transaction cannot be automatically retried"

    return True, "Policy check passed"
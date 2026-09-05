from datetime import datetime


def handle_payment_failure(transaction, action, failure_type):
    """
    Safely handle failures during recovery execution.
    """

    audit = {
        "timestamp": datetime.now().isoformat(),
        "transaction_id": transaction["transaction_id"],
        "requested_action": action,
        "failure_type": failure_type,
        "final_action": None,
        "status": None
    }

    # Payment API timeout
    if failure_type == "TIMEOUT":

        audit["status"] = "SAFE_STOP"
        audit["final_action"] = "ESCALATE"

        audit["message"] = (
            "Payment status could not be verified after API timeout. "
            "Further retries blocked and case escalated."
        )

        return audit

    # Unknown payment state
    if failure_type == "UNKNOWN_STATUS":

        audit["status"] = "SAFE_STOP"
        audit["final_action"] = "ESCALATE"

        audit["message"] = (
            "Payment state is uncertain. "
            "Automatic recovery stopped."
        )

        return audit

    audit["status"] = "FAILED"
    audit["final_action"] = "ESCALATE"
    audit["message"] = "Recovery action failed and was escalated."

    return audit
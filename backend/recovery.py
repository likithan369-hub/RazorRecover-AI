from datetime import datetime
from razorpay_service import create_test_order


def execute_recovery(transaction, action):

    # Escalation
    if action == "ESCALATE":
        return {
            "status": "ESCALATED",
            "message": "Case escalated to merchant",
            "recovered_amount": 0
        }

    # No action
    if action == "NO_ACTION":
        return {
            "status": "NO_ACTION",
            "message": "No recovery action taken",
            "recovered_amount": 0
        }

    # Send payment link using Razorpay Test Mode
    if action == "SEND_PAYMENT_LINK":

        order_result = create_test_order(
            amount=transaction["amount"],
            receipt=f"recovery_{transaction['transaction_id']}"
        )

        if order_result["success"]:

            return {
                "status": "PAYMENT_LINK_CREATED",
                "message": (
                    f"Razorpay Test Mode order created: "
                    f"{order_result['order_id']}"
                ),
                "recovered_amount": 0,
                "order_id": order_result["order_id"]
            }

        else:

            return {
                "status": "FAILED",
                "message": "Razorpay order creation failed",
                "recovered_amount": 0
            }

    # Retry payment
    if action == "RETRY_PAYMENT":

        recovered = int(transaction["recovered"]) == 1

        if recovered:
            return {
                "status": "SUCCESS",
                "message": "Payment retry succeeded",
                "recovered_amount": transaction["amount"]
            }

        return {
            "status": "FAILED",
            "message": "Payment retry did not recover payment",
            "recovered_amount": 0
        }

    # Reminder
    if action == "SEND_REMINDER":

        return {
            "status": "REMINDER_SENT",
            "message": "Payment reminder sent to customer",
            "recovered_amount": 0
        }

    # Unknown action
    return {
        "status": "FAILED",
        "message": "Unknown recovery action",
        "recovered_amount": 0
    }

def create_audit_record(transaction, probability, action, result):

    return {
        "timestamp": datetime.now().isoformat(),
        "transaction_id": transaction["transaction_id"],
        "amount": transaction["amount"],
        "recovery_probability": probability,
        "recommended_action": action,
        "execution_status": result["status"],
        "message": result["message"],
        "recovered_amount": result["recovered_amount"],
        "razorpay_order_id": result.get("order_id", "")
    }



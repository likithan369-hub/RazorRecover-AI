import os
import pandas as pd
import razorpay
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()


# ==========================================================
# AUDIT PATH
# ==========================================================

AUDIT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
    "audit_trail.csv"
)


# ==========================================================
# CHECK DUPLICATE RECOVERY
# ==========================================================

def check_duplicate_execution(transaction_id, action):
    """
    Prevent the same successful recovery action
    from being executed more than once.
    """

    if not os.path.exists(AUDIT_PATH):
        return False

    try:
        audit_df = pd.read_csv(AUDIT_PATH)

        required_columns = {
            "transaction_id",
            "recommended_action",
            "execution_status"
        }

        if not required_columns.issubset(audit_df.columns):
            return False

        matching = audit_df[
            (audit_df["transaction_id"].astype(str).str.strip() == str(transaction_id).strip())
            &
            (audit_df["recommended_action"].astype(str).str.strip() == action)
        ]

        # Successful recovery already exists
        successful_statuses = [
            "SUCCESS",
            "PAYMENT_SUCCESS",
            "PAYMENT_LINK_CREATED"
        ]

        if matching[
            matching["execution_status"].isin(successful_statuses)
        ].shape[0] > 0:
            return True

        return False

    except Exception as e:
        print(f"⚠️ Duplicate check failed: {e}")

        # Fail safe:
        # If audit verification fails, do NOT execute payment.
        return True


# ==========================================================
# SAVE AUDIT RECORD
# ==========================================================

def save_audit_record(transaction, action, result):

    new_record = {
        "timestamp": datetime.now().isoformat(),
        "transaction_id": transaction["transaction_id"],
        "amount": float(transaction["amount"]),
        "recovery_probability": "",
        "recommended_action": action,
        "execution_status": result["status"],
        "message": result["message"],
        "recovered_amount": result["recovered_amount"],
        "payment_link_id": result.get("payment_link_id")
    }

    new_df = pd.DataFrame([new_record])

    if os.path.exists(AUDIT_PATH):

        try:
            old_df = pd.read_csv(AUDIT_PATH)

            # Add missing columns
            for column in new_df.columns:
                if column not in old_df.columns:
                    old_df[column] = ""

            for column in old_df.columns:
                if column not in new_df.columns:
                    new_df[column] = ""

            new_df = new_df[old_df.columns]

            updated_df = pd.concat(
                [old_df, new_df],
                ignore_index=True
            )

        except Exception as e:

            print(
                f"⚠️ Could not read existing audit trail: {e}"
            )

            updated_df = new_df

    else:
        updated_df = new_df

    updated_df.to_csv(
        AUDIT_PATH,
        index=False
    )

    print(
        f"✅ Audit record saved for "
        f"{transaction['transaction_id']}"
    )


# ==========================================================
# EXECUTE RECOVERY
# ==========================================================

def execute_recovery(transaction, action):

    transaction_id = str(
        transaction["transaction_id"]
    ).strip()


    # ======================================================
    # DUPLICATE EXECUTION PROTECTION
    # ======================================================

    if check_duplicate_execution(
        transaction_id,
        action
    ):

        return {
            "status": "ALREADY_RECOVERED",
            "message": (
                f"Recovery already executed successfully "
                f"for transaction {transaction_id}. "
                f"Duplicate execution blocked."
            ),
            "recovered_amount": 0,
            "payment_link_id": None,
            "payment_link": None
        }


    # ======================================================
    # RETRY PAYMENT - TEST MODE
    # ======================================================

    if action == "RETRY_PAYMENT":

        recovered = int(
            transaction.get("recovered", 0)
        ) == 1

        if recovered:

            result = {
                "status": "SUCCESS",
                "message": (
                    "Payment retry succeeded in Test Mode."
                ),
                "recovered_amount": float(
                    transaction["amount"]
                ),
                "payment_link_id": None,
                "payment_link": None
            }

        else:

            result = {
                "status": "FAILED",
                "message": (
                    "Payment retry did not recover "
                    "the transaction."
                ),
                "recovered_amount": 0,
                "payment_link_id": None,
                "payment_link": None
            }

        save_audit_record(
            transaction,
            action,
            result
        )

        return result


    # ======================================================
    # SAFETY CHECK
    # ======================================================

    if action != "SEND_PAYMENT_LINK":

        return {
            "status": "SKIPPED",
            "message": "No payment action executed.",
            "recovered_amount": 0,
            "payment_link_id": None,
            "payment_link": None
        }


    # ======================================================
    # LOAD RAZORPAY CREDENTIALS
    # ======================================================

    key_id = os.getenv("RAZORPAY_KEY_ID")
    key_secret = os.getenv("RAZORPAY_KEY_SECRET")

    if not key_id or not key_secret:

        result = {
            "status": "FAILED",
            "message": "Razorpay API credentials not found.",
            "recovered_amount": 0,
            "payment_link_id": None,
            "payment_link": None
        }

        save_audit_record(
            transaction,
            action,
            result
        )

        return result


    # ======================================================
    # RAZORPAY PAYMENT LINK
    # ======================================================

    try:

        client = razorpay.Client(
            auth=(key_id, key_secret)
        )

        amount = float(
            transaction["amount"]
        )

        amount_paise = int(
            round(amount * 100)
        )

        reference_id = (
            f"REC-{transaction_id}-"
            f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        )

        reference_id = reference_id[:40]

        payment_link_data = {

            "amount": amount_paise,

            "currency": "INR",

            "accept_partial": False,

            "reference_id": reference_id,

            "description": (
                f"Recovery payment for "
                f"transaction {transaction_id}"
            ),

            "reminder_enable": True,

            "notes": {
                "transaction_id": transaction_id,
                "recovery_action": action
            }
        }


        payment_link = client.payment_link.create(
            data=payment_link_data
        )


        result = {

            "status": "PAYMENT_LINK_CREATED",

            "message": (
                "Razorpay payment link created successfully."
            ),

            "recovered_amount": 0,

            "payment_link_id": payment_link["id"],

            "payment_link": payment_link["short_url"]
        }


        save_audit_record(
            transaction,
            action,
            result
        )

        return result


    except Exception as e:

        result = {

            "status": "FAILED",

            "message": (
                f"Razorpay API error: {str(e)}"
            ),

            "recovered_amount": 0,

            "payment_link_id": None,

            "payment_link": None
        }

        save_audit_record(
            transaction,
            action,
            result
        )

        return result


# ==========================================================
# CHECK PAYMENT STATUS
# ==========================================================

def check_payment_status(payment_link_id):

    key_id = os.getenv("RAZORPAY_KEY_ID")
    key_secret = os.getenv("RAZORPAY_KEY_SECRET")

    if not key_id or not key_secret:

        return {
            "status": "FAILED",
            "message": "Razorpay API credentials not found.",
            "payment_status": "UNKNOWN",
            "paid_amount": 0
        }

    try:

        client = razorpay.Client(
            auth=(key_id, key_secret)
        )

        payment_link = client.payment_link.fetch(
            payment_link_id
        )

        link_status = payment_link.get(
            "status",
            "unknown"
        )

        amount_paid = payment_link.get(
            "amount_paid",
            0
        )

        paid_amount = amount_paid / 100


        if link_status.lower() == "paid":

            if os.path.exists(AUDIT_PATH):

                audit_df = pd.read_csv(
                    AUDIT_PATH
                )

                if "payment_link_id" in audit_df.columns:

                    audit_df["payment_link_id"] = (
                        audit_df["payment_link_id"]
                        .fillna("")
                        .astype(str)
                        .str.strip()
                    )

                    current_link_id = str(
                        payment_link_id
                    ).strip()

                    matching_rows = (
                        audit_df["payment_link_id"]
                        == current_link_id
                    )

                    if matching_rows.any():

                        audit_df.loc[
                            matching_rows,
                            "execution_status"
                        ] = "PAYMENT_SUCCESS"

                        audit_df.loc[
                            matching_rows,
                            "recovered_amount"
                        ] = paid_amount

                        audit_df.loc[
                            matching_rows,
                            "message"
                        ] = (
                            "Payment successfully received."
                        )

                        audit_df.to_csv(
                            AUDIT_PATH,
                            index=False
                        )

            return {
                "status": "SUCCESS",
                "message": "Payment successfully received.",
                "payment_status": "PAID",
                "paid_amount": paid_amount
            }


        return {
            "status": "PENDING",
            "message": (
                f"Payment Link status: {link_status}"
            ),
            "payment_status": link_status.upper(),
            "paid_amount": paid_amount
        }


    except Exception as e:

        return {
            "status": "FAILED",
            "message": f"Razorpay API error: {str(e)}",
            "payment_status": "UNKNOWN",
            "paid_amount": 0
        }
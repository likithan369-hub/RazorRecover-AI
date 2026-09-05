import joblib
import pandas as pd


MODEL_PATH = "models/recovery_model.pkl"

model = joblib.load(MODEL_PATH)


def predict_recovery(transaction):
    """
    Predict probability that a revenue-at-risk transaction
    can be recovered.
    """

    df = pd.DataFrame([transaction])

    # Make sure categorical columns are strings
    categorical_columns = [
        "payment_method",
        "transaction_status",
        "failure_reason",
        "customer_value"
    ]

    for column in categorical_columns:
        df[column] = df[column].astype(str)

    probability = model.predict_proba(df)[0][1]

    return round(float(probability), 4)


def choose_intervention(transaction, probability):

    retry_count = transaction["retry_count"]
    amount = transaction["amount"]
    status = transaction["transaction_status"]

    # HARD SAFETY LIMIT
    if retry_count >= 3:
        return "ESCALATE"

    # High-value transactions need extra caution
    if amount >= 30000:
        if probability >= 0.60 and retry_count < 2:
            return "RETRY_PAYMENT"
        elif probability >= 0.35:
            return "SEND_PAYMENT_LINK"
        else:
            return "ESCALATE"

    # Failed payment
    if status == "Failed":

        if probability >= 0.55 and retry_count < 2:
            return "RETRY_PAYMENT"

        elif probability >= 0.25:
            return "SEND_PAYMENT_LINK"

        else:
            return "ESCALATE"

    # Abandoned checkout
    if status == "Abandoned":

        if probability >= 0.50:
            return "SEND_PAYMENT_LINK"

        elif probability >= 0.20:
            return "SEND_REMINDER"

        else:
            return "ESCALATE"

    # Failed subscription
    if status == "Subscription_Failed":

        if probability >= 0.55 and retry_count < 2:
            return "RETRY_PAYMENT"

        elif probability >= 0.25:
            return "SEND_REMINDER"

        else:
            return "ESCALATE"

    # Overdue
    if status == "Overdue":

        if probability >= 0.45:
            return "SEND_REMINDER"

        elif probability >= 0.25:
            return "SEND_PAYMENT_LINK"

        else:
            return "ESCALATE"

    return "NO_ACTION"
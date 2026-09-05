import os
import razorpay
from dotenv import load_dotenv

load_dotenv()

KEY_ID = os.getenv("RAZORPAY_KEY_ID")
KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

client = razorpay.Client(
    auth=(KEY_ID, KEY_SECRET)
)


def create_test_order(amount, receipt):
    """
    Create a Razorpay Test Mode order.

    Amount is provided in rupees.
    Razorpay expects amount in paise.
    """

    amount_paise = int(amount * 100)

    order_data = {
        "amount": amount_paise,
        "currency": "INR",
        "receipt": receipt
    }

    try:
        order = client.order.create(data=order_data)

        return {
            "success": True,
            "order_id": order["id"],
            "amount": order["amount"],
            "currency": order["currency"],
            "receipt": order["receipt"]
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }
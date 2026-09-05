import os
from dotenv import load_dotenv
import razorpay

load_dotenv()

key_id = os.getenv("RAZORPAY_KEY_ID")
key_secret = os.getenv("RAZORPAY_KEY_SECRET")

print("===== RAZORPAY CONNECTION TEST =====")

if not key_id:
    print("❌ RAZORPAY_KEY_ID not found")
    exit()

if not key_secret:
    print("❌ RAZORPAY_KEY_SECRET not found")
    exit()

print("✅ Key ID loaded")
print("✅ Key Secret loaded")

client = razorpay.Client(
    auth=(key_id, key_secret)
)

print("✅ Razorpay client initialized")
print("===== TEST PASSED =====")
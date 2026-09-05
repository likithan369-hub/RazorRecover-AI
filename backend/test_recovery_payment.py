from razorpay_service import create_test_order


print("===== RAZORRECOVER AI =====")
print("Razorpay Test Mode Recovery Demo")
print()


# Representative transaction
transaction_id = "TX00020"
amount = 3676.07

print(f"Transaction: {transaction_id}")
print(f"Amount at risk: ₹{amount:,.2f}")

print("\nAI Recommendation: SEND_PAYMENT_LINK")
print("Guardrail: ALLOWED")

print("\n===== RAZORPAY TEST MODE =====")

result = create_test_order(
    amount=amount,
    receipt=f"recovery_{transaction_id}"
)

if result["success"]:

    print("✅ Recovery order created")

    print(f"Order ID: {result['order_id']}")
    print(f"Amount: ₹{result['amount'] / 100:.2f}")
    print(f"Currency: {result['currency']}")

    print("\nStatus: PAYMENT_LINK_CREATED")

else:

    print("❌ Razorpay order creation failed")
    print(f"Error: {result['error']}")
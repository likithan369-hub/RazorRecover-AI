from razorpay_service import create_test_order


print("===== RAZORPAY TEST ORDER =====")

result = create_test_order(
    amount=100,
    receipt="razorrecover_test_001"
)

if result["success"]:

    print("✅ Order created successfully")
    print(f"Order ID: {result['order_id']}")
    print(f"Amount: ₹{result['amount'] / 100:.2f}")
    print(f"Currency: {result['currency']}")
    print(f"Receipt: {result['receipt']}")

else:

    print("❌ Order creation failed")
    print(result["error"])
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, roc_auc_score

# Load dataset
data = pd.read_csv("data/transactions.csv")

# Features
features = [
    "amount",
    "payment_method",
    "transaction_status",
    "failure_reason",
    "retry_count",
    "previous_success_rate",
    "customer_value",
    "checkout_duration",
    "days_overdue"
]

X = data[features]
y = data["recovered"]

# Categorical and numerical columns
categorical_features = [
    "payment_method",
    "transaction_status",
    "failure_reason",
    "customer_value"
]

numerical_features = [
    "amount",
    "retry_count",
    "previous_success_rate",
    "checkout_duration",
    "days_overdue"
]

# Preprocessing
preprocessor = ColumnTransformer(
    transformers=[
        (
            "cat",
            OneHotEncoder(handle_unknown="ignore"),
            categorical_features
        ),
        (
            "num",
            "passthrough",
            numerical_features
        )
    ]
)

# Model
model = RandomForestClassifier(
    n_estimators=200,
    max_depth=12,
    random_state=42,
    class_weight="balanced"
)

# Pipeline
pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("model", model)
])

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

# Train
pipeline.fit(X_train, y_train)

# Predictions
predictions = pipeline.predict(X_test)
probabilities = pipeline.predict_proba(X_test)[:, 1]

# Evaluation
print("\nMODEL PERFORMANCE")
print("=" * 50)

print(classification_report(y_test, predictions))

print(
    f"ROC-AUC: "
    f"{roc_auc_score(y_test, probabilities):.4f}"
)

# Save model
joblib.dump(
    pipeline,
    "models/recovery_model.pkl"
)

print("\nModel saved successfully!")
print("models/recovery_model.pkl")
"""
One-time MongoDB setup script: creates useful indexes for the churn prediction system.

Run with:  python mongo_init.py
(from the backend/ directory, with your virtualenv active and .env configured)
"""
from app.database import (
    datasets_collection, customers_collection, models_collection,
    predictions_collection, history_collection, check_connection
)


def main():
    if not check_connection():
        print("ERROR: Could not connect to MongoDB. Check MONGO_URI in your .env file.")
        return

    datasets_collection.create_index("dataset_id", unique=True)
    customers_collection.create_index("dataset_id")
    models_collection.create_index("model_id", unique=True)
    models_collection.create_index("dataset_id")
    predictions_collection.create_index("prediction_id", unique=True)
    predictions_collection.create_index("predicted_at")
    history_collection.create_index("run_at")

    print("MongoDB connected successfully. Indexes created for:")
    print(" - datasets.dataset_id (unique)")
    print(" - customers.dataset_id")
    print(" - models.model_id (unique), models.dataset_id")
    print(" - predictions.prediction_id (unique), predictions.predicted_at")
    print(" - analysis_history.run_at")


if __name__ == "__main__":
    main()

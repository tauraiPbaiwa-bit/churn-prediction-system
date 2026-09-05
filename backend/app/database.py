"""
MongoDB connection and collection accessors.
Uses PyMongo (sync) for simplicity in an academic project context.
"""
from pymongo import MongoClient
from app.config import settings

_client = MongoClient(settings.mongo_uri)
db = _client[settings.mongo_db_name]

# Collections
datasets_collection = db["datasets"]          # metadata about uploaded datasets
customers_collection = db["customers"]        # cleaned customer records per dataset
models_collection = db["models"]              # trained model metadata & metrics
predictions_collection = db["predictions"]    # individual + batch prediction results
history_collection = db["analysis_history"]   # OLAP / analysis run history


def check_connection() -> bool:
    try:
        _client.admin.command("ping")
        return True
    except Exception:
        return False

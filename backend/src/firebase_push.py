"""Push karma scores into Firebase Realtime Database."""

from __future__ import annotations

from typing import Optional

import firebase_admin
from firebase_admin import credentials, db

from .config import FIREBASE_DB_URL, SERVICE_ACCOUNT_PATH
from .modeling import run_inference
from .utils import configure_logging

LOGGER = configure_logging("firebase")


def init_firebase(service_account: Optional[str] = None, db_url: Optional[str] = None) -> None:
    """Initialize Firebase Admin SDK if not already configured."""

    if firebase_admin._apps:
        return

    service_account_path = service_account or SERVICE_ACCOUNT_PATH
    db_url = db_url or FIREBASE_DB_URL
    if not service_account_path.exists():
        raise FileNotFoundError(
            f"Firebase service account json missing at {service_account_path}."
        )
    if not db_url:
        raise ValueError("FIREBASE_DB_URL is not set. Provide it via env or CLI.")

    cred = credentials.Certificate(service_account_path)
    firebase_admin.initialize_app(cred, {"databaseURL": db_url})
    LOGGER.info("Initialized Firebase app for %s", db_url)


def push_scores(
    service_account: Optional[str] = None,
    db_url: Optional[str] = None,
    node: str = "karma",
) -> None:
    """Run inference and push the latest karma scores to Firebase."""

    init_firebase(service_account, db_url)
    per_lap = run_inference()
    LOGGER.info("Pushing %s rows to Firebase/%s", len(per_lap), node)

    reference = db.reference(f"/{node}")
    payload = {}
    for _, row in per_lap.iterrows():
        vehicle_id = str(row["vehicle_id"]).strip()
        payload[vehicle_id] = {
            "vehicle_id": vehicle_id,
            "lap": int(row["lap"]),
            "karma_score": float(row["karma_score"]),
            "status": row.get("STATUS"),
        }
    reference.update(payload)
    LOGGER.info("Firebase update complete.")


__all__ = ["push_scores", "init_firebase"]

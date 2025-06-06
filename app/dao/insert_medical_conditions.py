# app/services/insert_conditions.py
from sqlalchemy.orm import Session
from app.models.core import Condition

def get_or_create_condition(db: Session, condition_name: str) -> int:
    """
    Fetch existing condition by name (case insensitive).
    If not exists, create new and return its id.
    """
    condition_name_lower = condition_name.lower()
    condition = db.query(Condition).filter(
        Condition.condition_name.ilike(condition_name_lower)
    ).first()
    if condition:
        print("Fetched condition ID:", condition.condition_id)
        return condition.condition_id

    new_condition = Condition(condition_name=condition_name_lower)
    db.add(new_condition)
    db.commit()
    db.refresh(new_condition)
    print("created condition ID:", new_condition.condition_id)
    return new_condition.condition_id

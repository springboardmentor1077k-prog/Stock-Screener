# Alerts API Router
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ...models.schemas import AlertCreate
from ...database.connection import get_db
from ...services.alert_service import AlertService
from ...auth.jwt_handler import get_current_user
from ...models.database import User

alerts_router = APIRouter()

@alerts_router.get("/", response_model=List[dict])
def get_user_alerts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Get user's alerts.
    """
    from ...core.utils import handle_database_error
    
    try:
        service = AlertService()
        return service.get_user_alerts(current_user.user_id, db)
    except Exception as e:
        handle_database_error(e)

@alerts_router.post("/create")
def create_alert(alert: AlertCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Create a new alert for user.
    """
    from ...core.utils import handle_database_error
    
    try:
        service = AlertService()
        # Create the alert directly with the provided stock_id.
        # This keeps the endpoint flexible for your current UI, while
        # the service layer handles any database-level issues.
        success = service.create_alert(
            current_user.user_id,
            alert.stock_id,
            alert.condition_type,
            alert.condition_value,
            db,
        )
        if success:
            return {"message": f"Created alert for stock {alert.stock_id} with condition {alert.condition_type} {alert.condition_value}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to create alert")
    except Exception as e:
        handle_database_error(e)

@alerts_router.put("/{alert_id}/toggle")
def toggle_alert(alert_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Toggle alert status (active/inactive).
    """
    from ...core.utils import handle_database_error
    from ...models.database import Alert
    
    try:
        service = AlertService()
        # Get the current alert status
        alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        # Toggle the status
        new_status = not alert.is_active
        success = service.update_alert_status(alert_id, new_status, db)
        if success:
            return {"message": f"Toggled alert {alert_id} status to {'active' if new_status else 'inactive'}", "new_status": new_status}
        else:
            raise HTTPException(status_code=500, detail="Failed to update alert status")
    except Exception as e:
        handle_database_error(e)

@alerts_router.delete("/{alert_id}")
def delete_alert(alert_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Delete an alert.
    """
    from ...core.utils import handle_database_error
    
    try:
        service = AlertService()
        success = service.delete_alert(alert_id, db)
        if success:
            return {"message": f"Deleted alert {alert_id}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete alert")
    except Exception as e:
        handle_database_error(e)

@alerts_router.get("/triggered", response_model=List[dict])
def get_triggered_alerts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Get triggered alerts for user.
    """
    from ...core.utils import handle_database_error
    
    try:
        service = AlertService()
        return service.get_triggered_alerts(current_user.user_id, db)
    except Exception as e:
        handle_database_error(e)
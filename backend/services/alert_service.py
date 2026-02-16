# Alert Service
import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from ..models.database import Alert, User, MasterStock, Fundamental
from sqlalchemy import and_
from datetime import datetime

logger = logging.getLogger(__name__)


class AlertService:
    def __init__(self):
        pass
    
    def get_user_alerts(self, user_id: str, db: Session) -> List[Dict[str, Any]]:
        """Get user's alerts.

        Uses a LEFT JOIN so alerts are still visible even if the related
        stock record is missing, falling back to the raw stock_id.
        """
        alerts = (
            db.query(Alert, MasterStock)
            .outerjoin(MasterStock, Alert.stock_id == MasterStock.stock_id)
            .filter(Alert.user_id == user_id)
            .all()
        )

        results: List[Dict[str, Any]] = []
        for alert, stock in alerts:
            results.append(
                {
                    "alert_id": alert.alert_id,
                    "stock_id": alert.stock_id,
                    "symbol": stock.symbol if stock else None,
                    "company_name": stock.company_name if stock else None,
                    "condition_type": alert.condition_type,
                    "condition_value": float(alert.condition_value) if alert.condition_value else None,
                    "is_active": alert.is_active,
                    "created_at": alert.created_at,
                    "triggered_at": alert.triggered_at,
                }
            )

        return results
    
    def create_alert(self, user_id: str, stock_id: str, condition_type: str, condition_value: float, db: Session) -> bool:
        """Create a new alert for user"""
        try:
            alert = Alert(
                user_id=user_id,
                stock_id=stock_id,
                condition_type=condition_type,
                condition_value=condition_value,
                is_active=True
            )
            db.add(alert)
            db.commit()
            db.refresh(alert)  # Refresh to get the created alert ID
            return True
        except Exception as e:
            logger.error(f"Error creating alert: {str(e)}", exc_info=True)
            db.rollback()
            return False
    
    def update_alert_status(self, alert_id: str, is_active: bool, db: Session) -> bool:
        """Toggle alert status (active/inactive)"""
        try:
            alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
            if alert:
                alert.is_active = is_active
                alert.updated_at = datetime.utcnow()
                db.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating alert status: {str(e)}", exc_info=True)
            db.rollback()
            return False
    
    def delete_alert(self, alert_id: str, db: Session) -> bool:
        """Delete an alert"""
        try:
            alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
            if alert:
                db.delete(alert)
                db.commit()
            return True
        except Exception as e:
            logger.error(f"Error deleting alert: {str(e)}", exc_info=True)
            db.rollback()
            return False
    
    def get_triggered_alerts(self, user_id: str, db: Session) -> List[Dict[str, Any]]:
        """Get triggered alerts for user"""
        alerts = db.query(Alert, MasterStock, Fundamental).\
            join(MasterStock, Alert.stock_id == MasterStock.stock_id).\
            join(Fundamental, Alert.stock_id == Fundamental.stock_id).\
            filter(Alert.user_id == user_id, Alert.triggered_at.isnot(None)).\
            all()
        
        results = []
        for alert, stock, fundamental in alerts:
            results.append({
                "alert_id": alert.alert_id,
                "stock_id": stock.stock_id,
                "symbol": stock.symbol,
                "company_name": stock.company_name,
                "condition_type": alert.condition_type,
                "condition_value": float(alert.condition_value) if alert.condition_value else None,
                "current_value": self._get_current_value(alert.condition_type, fundamental),
                "triggered_at": alert.triggered_at,
            })
        
        return results
    
    def check_active_alerts(self, db: Session) -> List[Dict[str, Any]]:
        """Check all active alerts against current market data"""
        alerts = db.query(Alert, MasterStock, Fundamental).\
            join(MasterStock, Alert.stock_id == MasterStock.stock_id).\
            join(Fundamental, Alert.stock_id == Fundamental.stock_id).\
            filter(Alert.is_active == True).\
            all()
        
        triggered_alerts = []
        for alert, stock, fundamental in alerts:
            current_value = self._get_current_value(alert.condition_type, fundamental)
            
            if self._should_trigger_alert(alert, current_value):
                triggered_alerts.append({
                    "alert_id": alert.alert_id,
                    "user_id": alert.user_id,
                    "stock_id": stock.stock_id,
                    "symbol": stock.symbol,
                    "condition_type": alert.condition_type,
                    "condition_value": float(alert.condition_value),
                    "current_value": current_value,
                })
        
        return triggered_alerts
    
    def _get_current_value(self, condition_type: str, fundamental: Fundamental) -> float:
        """Get the current value for a given condition type"""
        if "PE" in condition_type.upper():
            return float(fundamental.pe_ratio) if fundamental.pe_ratio else 0
        elif "PEG" in condition_type.upper():
            return float(fundamental.peg_ratio) if fundamental.peg_ratio else 0
        elif "PRICE" in condition_type.upper():
            return float(fundamental.current_price) if fundamental.current_price else 0
        elif "EBITDA" in condition_type.upper():
            return float(fundamental.ebitda) if fundamental.ebitda else 0
        elif "CASH_FLOW" in condition_type.upper():
            return float(fundamental.free_cash_flow) if fundamental.free_cash_flow else 0
        
        # Default to current price if no specific match
        return float(fundamental.current_price) if fundamental.current_price else 0
    
    def _should_trigger_alert(self, alert: Alert, current_value: float) -> bool:
        """Check if an alert should be triggered based on current value"""
        condition_type = alert.condition_type.upper()
        threshold_value = float(alert.condition_value) if alert.condition_value else 0
        
        if "BELOW" in condition_type or "UNDER" in condition_type or "LESS_THAN" in condition_type:
            return current_value < threshold_value
        elif "ABOVE" in condition_type or "OVER" in condition_type or "GREATER_THAN" in condition_type:
            return current_value > threshold_value
        elif "EQUAL" in condition_type:
            return current_value == threshold_value
        
        # Default behavior - return False if condition type is not recognized
        return False
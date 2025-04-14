from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from collections import defaultdict
from .models import Purchase, Session
import pandas as pd

class RecommendationSystem:
    def __init__(self, db: Session):
        self.db = db
        
    def get_frequently_bought_together(self, item_id, limit=5):
        # Trouve les articles fréquemment achetés ensemble
        query = self.db.query(
            Purchase.item_id,
            func.count().label('count')
        ).filter(
            Purchase.session_id.in_(
                self.db.query(Purchase.session_id).filter(
                    Purchase.item_id == item_id
                )
            ),
            Purchase.item_id != item_id
        ).group_by(
            Purchase.item_id
        ).order_by(
            desc('count')
        ).limit(limit)
        
        return [{"item_id": item.item_id, "score": item.count} for item in query]
    
    def get_view_to_purchase_recommendations(self, item_id, limit=5):
        # Recommandations basées sur ce que les gens achètent après avoir vu cet article
        sessions_with_item = self.db.query(Session.session_id).filter(
            Session.item_id == item_id
        ).distinct()
        
        purchases_after_view = self.db.query(
            Purchase.item_id,
            func.count().label('count')
        ).filter(
            Purchase.session_id.in_(sessions_with_item),
            Purchase.item_id != item_id
        ).group_by(
            Purchase.item_id
        ).order_by(
            desc('count')
        ).limit(limit)
        
        return [{"item_id": item.item_id, "score": item.count} for item in purchases_after_view]

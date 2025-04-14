from sqlalchemy.orm import Session
from sqlalchemy import func, desc, text
from collections import defaultdict
from .models import Purchase, Session
from .item_validator import ItemValidator
import pandas as pd

class ProductRecommender:
    def __init__(self, db: Session):
        self.db = db
        self.validator = ItemValidator(db)
        
    def recommend_for_product(self, item_id, num_recommendations=5):
        """Recommande des produits basés sur un seul produit d'entrée"""
        # Vérifier si l'item existe
        if not self.validator.item_exists(item_id):
            print(f"L'item {item_id} n'existe pas dans la base de données")
            return []
            
        # Combine plusieurs stratégies de recommandation
        bought_together = self.get_frequently_bought_together(item_id, limit=num_recommendations)
        view_purchase = self.get_view_to_purchase_recommendations(item_id, limit=num_recommendations)
        
        # Fusionner et trier les recommandations
        recommendations = self._merge_recommendations([bought_together, view_purchase])
        return recommendations[:num_recommendations]
    
    def recommend_for_products(self, item_ids, num_recommendations=5):
        """Recommande des produits basés sur plusieurs produits d'entrée"""
        print(f"Recherche de recommandations pour les items {item_ids}")
        
        # Vérifier si tous les items existent
        if not self.validator.items_exist(item_ids):
            print(f"Un ou plusieurs items parmi {item_ids} n'existent pas dans la base de données")
            return []
        
        # Requête simplifiée sans contrainte de date
        query = text("""
            SELECT p2.item_id, COUNT(*) as score
            FROM purchases p1
            JOIN purchases p2 ON p1.session_id = p2.session_id
            WHERE p1.item_id IN :item_ids
            AND p2.item_id NOT IN :item_ids
            GROUP BY p2.item_id
            ORDER BY score DESC
            LIMIT :limit
        """)
        
        result = self.db.execute(query, {"item_ids": tuple(item_ids), "limit": num_recommendations})
        recommendations = [{"item_id": row[0], "score": row[1]} for row in result]
        print(f"Nombre de recommandations trouvées: {len(recommendations)}")
        
        return recommendations
    
    def get_frequently_bought_together(self, item_id, limit=5):
        print(f"Recherche de recommandations pour l'item {item_id}")
        
        # Vérifier d'abord s'il y a des achats pour cet item
        check_query = text("SELECT COUNT(*) FROM purchases WHERE item_id = :item_id")
        count = self.db.execute(check_query, {"item_id": item_id}).scalar()
        print(f"Nombre d'achats trouvés pour l'item {item_id}: {count}")
        
        if count == 0:
            print("Aucun achat trouvé pour cet item")
            return []
            
        # Requête simplifiée sans contrainte de date
        query = text("""
            SELECT p2.item_id, COUNT(*) as score
            FROM purchases p1
            JOIN purchases p2 ON p1.session_id = p2.session_id
            WHERE p1.item_id = :item_id
            AND p2.item_id <> :item_id
            GROUP BY p2.item_id
            ORDER BY score DESC
            LIMIT :limit
        """)
        
        result = self.db.execute(query, {"item_id": item_id, "limit": limit})
        recommendations = [{"item_id": row[0], "score": row[1]} for row in result]
        print(f"Nombre de recommandations trouvées: {len(recommendations)}")
        
        
        return recommendations
    
    def get_sequential_view_recommendations(self, item_id, limit=5):
        """Recommande des produits basés sur la séquence de navigation"""
        query = text("""
            SELECT s2.item_id, COUNT(*) as score
            FROM sessions s1
            JOIN sessions s2 ON s1.session_id = s2.session_id
            WHERE s1.item_id = :item_id
            AND s2.item_id <> :item_id
            AND s2.view_date > s1.view_date
            AND s1.view_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
            GROUP BY s2.item_id
            ORDER BY score DESC
            LIMIT :limit
        """)
        result = self.db.execute(query, {"item_id": item_id, "limit": limit})
        
        return [{"item_id": row[0], "score": row[1]} for row in result]
    
    def get_view_to_purchase_recommendations(self, item_id, limit=5):
        # Utilisation des vues matérialisées
        query = text("""
            SELECT recommended_item_id as item_id, score
            FROM product_recommendations
            WHERE source_item_id = :item_id
            AND recommendation_type = 'VIEW_TO_PURCHASE'
            AND last_updated >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
            ORDER BY score DESC
            LIMIT :limit
        """)
        
        result = self.db.execute(query, {"item_id": item_id, "limit": limit})
        recommendations = [{"item_id": row[0], "score": row[1]} for row in result]
        
        # Si pas de recommandations dans la vue matérialisée, utiliser la requête directe
        if not recommendations:
            query = text("""
                SELECT p.item_id, COUNT(*) as score
                FROM sessions s
                JOIN purchases p ON s.session_id = p.session_id
                WHERE s.item_id = :item_id
                AND p.item_id <> :item_id
                AND s.view_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
                GROUP BY p.item_id
                ORDER BY score DESC
                LIMIT :limit
            """)
            result = self.db.execute(query, {"item_id": item_id, "limit": limit})
            recommendations = [{"item_id": row[0], "score": row[1]} for row in result]
        
        return recommendations
    
    def _merge_recommendations(self, recommendation_lists):
        """Fusionne plusieurs listes de recommandations en tenant compte des scores"""
        merged = {}
        for rec_list in recommendation_lists:
            for rec in rec_list:
                item_id = rec["item_id"]
                if item_id in merged:
                    merged[item_id]["score"] += rec["score"]
                else:
                    merged[item_id] = rec
        
        # Trier par score
        return sorted(merged.values(), key=lambda x: x["score"], reverse=True)

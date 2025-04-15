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
            return []
            
        # Requête SQL optimisée combinant plusieurs stratégies dans une seule opération
        query = text("""
            WITH recent_interactions AS (
                SELECT item_id, MAX(event_date) as last_interaction FROM (
                    SELECT p2.item_id, p2.purchase_date as event_date
                    FROM purchases p1
                    JOIN purchases p2 ON p1.session_id = p2.session_id
                    WHERE p1.item_id = :item_id AND p2.item_id <> :item_id
                    
                    UNION ALL
                    
                    SELECT s2.item_id, s2.view_date as event_date
                    FROM sessions s1
                    JOIN sessions s2 ON s1.session_id = s2.session_id
                    WHERE s1.item_id = :item_id AND s2.item_id <> :item_id
                ) all_events
                GROUP BY item_id
            ),
            bought_together AS (
                SELECT 
                    p2.item_id, 
                    COUNT(*) as bt_score,
                    COUNT(DISTINCT p1.session_id) as unique_sessions
                FROM purchases p1
                JOIN purchases p2 ON p1.session_id = p2.session_id
                WHERE p1.item_id = :item_id
                AND p2.item_id <> :item_id
                AND p1.purchase_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
                GROUP BY p2.item_id
            ),
            view_purchase AS (
                SELECT 
                    p.item_id,
                    COUNT(*) as vp_score
                FROM sessions s
                JOIN purchases p 
                    ON s.session_id = p.session_id
                    AND s.view_date < p.purchase_date
                WHERE s.item_id = :item_id
                AND p.item_id <> :item_id
                GROUP BY p.item_id
            )
            SELECT 
                COALESCE(bt.item_id, vp.item_id) as item_id,
                (COALESCE(bt.bt_score, 0) * 2) + 
                (COALESCE(bt.unique_sessions, 0) * 1.5) + 
                (COALESCE(vp.vp_score, 0) * 3) as score,
                ri.last_interaction
            FROM 
                bought_together bt
            FULL OUTER JOIN 
                view_purchase vp ON bt.item_id = vp.item_id
            LEFT JOIN
                recent_interactions ri ON COALESCE(bt.item_id, vp.item_id) = ri.item_id
            ORDER BY 
                score DESC,
                last_interaction DESC NULLS LAST
            LIMIT :limit
        """)
        
        try:
            # Utiliser une version compatible avec MySQL si nécessaire
            result = self.db.execute(query, {"item_id": item_id, "limit": num_recommendations})
            recommendations = [{"item_id": row[0], "score": row[1]} for row in result]
        except Exception as e:
            print(f"❌ Erreur SQL: {str(e)}. Essai avec une requête alternative.")
            # Version alternative compatible avec MySQL
            query_alt = text("""
                WITH recent_events AS (
                    SELECT item_id, event_date FROM (
                        SELECT p2.item_id, p2.purchase_date as event_date
                        FROM purchases p1
                        JOIN purchases p2 ON p1.session_id = p2.session_id
                        WHERE p1.item_id = :item_id AND p2.item_id <> :item_id
                        AND p1.purchase_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
                        
                        UNION ALL
                        
                        SELECT s2.item_id, s2.view_date as event_date
                        FROM sessions s1
                        JOIN sessions s2 ON s1.session_id = s2.session_id
                        WHERE s1.item_id = :item_id AND s2.item_id <> :item_id
                    ) all_events
                )
                SELECT 
                    c.item_id,
                    c.total_score as score,
                    MAX(re.event_date) as last_interaction
                FROM (
                    SELECT item_id, COUNT(*) * 2 as total_score
                    FROM purchases p1
                    JOIN purchases p2 ON p1.session_id = p2.session_id
                    WHERE p1.item_id = :item_id
                    AND p2.item_id <> :item_id
                    GROUP BY p2.item_id
                    
                    UNION ALL
                    
                    SELECT p.item_id, COUNT(*) as total_score
                    FROM sessions s
                    JOIN purchases p ON s.session_id = p.session_id
                    WHERE s.item_id = :item_id
                    AND p.item_id <> :item_id
                    AND s.view_date < p.purchase_date
                    GROUP BY p.item_id
                ) c
                LEFT JOIN recent_events re ON c.item_id = re.item_id
                GROUP BY c.item_id, c.total_score
                ORDER BY score DESC, last_interaction DESC NULLS LAST
                LIMIT :limit
            """)
            result = self.db.execute(query_alt, (item_id, item_id, item_id, item_id, num_recommendations))
            recommendations = [{"item_id": row[0], "score": row[1]} for row in result]
            
        return recommendations
    
    def recommend_for_products(self, item_ids, num_recommendations=5):
        """Recommande des produits basés sur plusieurs produits d'entrée"""
        # Vérifier si les items existent et obtenir la liste des items valides
        all_exist, valid_items = self.validator.items_exist(item_ids)
        
        if not valid_items:
            return []
        
        # Requête avec filtrage temporel et détection de séquences d'achat
        query = text("""
            -- Produits achetés ensemble
            WITH purchase_together AS (
                SELECT 
                    p2.item_id, 
                    COUNT(*) as together_score,
                    COUNT(DISTINCT p1.session_id) as unique_sessions
                FROM purchases p1
                JOIN purchases p2 ON p1.session_id = p2.session_id
                WHERE p1.item_id IN :item_ids
                AND p2.item_id NOT IN :item_ids
                -- Filtre sur les 90 derniers jours pour la pertinence temporelle
                AND p1.purchase_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
                GROUP BY p2.item_id
            ),
            -- Détection de séquences (consulté puis acheté)
            sequence_patterns AS (
                SELECT 
                    p.item_id,
                    COUNT(*) as sequence_score
                FROM sessions s
                JOIN purchases p 
                    ON s.session_id = p.session_id
                    -- Assurez-vous que la consultation a précédé l'achat
                    AND s.view_date < p.purchase_date
                WHERE s.item_id IN :item_ids
                AND p.item_id NOT IN :item_ids
                GROUP BY p.item_id
            )
            -- Combinaison des scores avec pondération
            SELECT 
                COALESCE(pt.item_id, sp.item_id) as item_id,
                (COALESCE(pt.together_score, 0) * 2) + 
                (COALESCE(pt.unique_sessions, 0) * 1.5) + 
                (COALESCE(sp.sequence_score, 0) * 3) as weighted_score
            FROM 
                purchase_together pt
            LEFT JOIN 
                sequence_patterns sp ON pt.item_id = sp.item_id
            ORDER BY 
                weighted_score DESC
            LIMIT :limit
        """)
        
        try:
            result = self.db.execute(query, {
                "item_ids": tuple(valid_items), 
                "limit": num_recommendations
            })
            recommendations = [{"item_id": row[0], "score": float(row[1])} for row in result]
        except Exception as e:
            print(f"❌ Erreur SQL: {str(e)}. Essai avec une requête alternative.")
            # Version simplifiée compatible avec MySQL
            query_alt = text("""
                SELECT p2.item_id, COUNT(*) as score
                FROM purchases p1
                JOIN purchases p2 ON p1.session_id = p2.session_id
                WHERE p1.item_id IN :item_ids
                AND p2.item_id NOT IN :item_ids
                GROUP BY p2.item_id
                ORDER BY score DESC
                LIMIT :limit
            """)
            result = self.db.execute(query_alt, {
                "item_ids": tuple(valid_items), 
                "limit": num_recommendations
            })
            recommendations = [{"item_id": row[0], "score": row[1]} for row in result]
            
        return recommendations
    
    def get_purchase_paths(self, item_id, max_path_length=3, min_support=2):
        """Détermine les parcours d'achat typiques incluant l'item spécifié"""
        if not self.validator.item_exists(item_id):
            return []
            
        # Requête pour extraire les séquences de consultation avant achat
        query = text("""
            SELECT 
                s1.session_id,
                s1.item_id as viewed_item,
                s1.view_date,
                p.item_id as purchased_item,
                p.purchase_date
            FROM 
                sessions s1
            JOIN 
                purchases p ON s1.session_id = p.session_id
            WHERE 
                -- Limiter aux sessions qui incluent l'item d'intérêt
                s1.session_id IN (
                    SELECT DISTINCT session_id 
                    FROM sessions 
                    WHERE item_id = :item_id
                )
                -- S'assurer que la consultation précède l'achat
                AND s1.view_date < p.purchase_date
            ORDER BY 
                s1.session_id, s1.view_date
        """)
        
        result = self.db.execute(query, {"item_id": item_id})
        
        # Traitement Python pour analyser les parcours
        session_paths = {}
        for row in result:
            session_id = row[0]
            viewed_item = row[1]
            purchased_item = row[3]
            
            if session_id not in session_paths:
                session_paths[session_id] = {"views": [], "purchase": purchased_item}
            
            session_paths[session_id]["views"].append(viewed_item)
        
        # Limiter les chemins à max_path_length éléments
        for session_id, data in session_paths.items():
            data["views"] = data["views"][:max_path_length]
        
        # Compter la fréquence des chemins
        path_counts = {}
        for data in session_paths.values():
            path = tuple(data["views"] + [data["purchase"]])
            if path in path_counts:
                path_counts[path] += 1
            else:
                path_counts[path] = 1
        
        # Filtrer par support minimum et trier par fréquence
        frequent_paths = [
            {"path": list(path), "frequency": count}
            for path, count in path_counts.items()
            if count >= min_support
        ]
        
        return sorted(frequent_paths, key=lambda x: x["frequency"], reverse=True)

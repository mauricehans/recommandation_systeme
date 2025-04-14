from sqlalchemy import text
from sqlalchemy.orm import Session

class ItemValidator:
    def __init__(self, db: Session):
        self.db = db
    
    def item_exists(self, item_id):
        """Vérifie si un item existe dans la base de données"""
        try:
            # Vérifier dans la table purchases
            purchases_query = text("SELECT COUNT(*) FROM purchases WHERE item_id = :item_id")
            purchases_count = self.db.execute(purchases_query, {"item_id": item_id}).scalar()
            
            # Vérifier dans la table sessions
            sessions_query = text("SELECT COUNT(*) FROM sessions WHERE item_id = :item_id")
            sessions_count = self.db.execute(sessions_query, {"item_id": item_id}).scalar()
            
            exists = purchases_count > 0 or sessions_count > 0
            print(f"Validation de l'item {item_id}: "
                  f"Trouvé dans {purchases_count} achats et {sessions_count} sessions")
            
            return exists
        except Exception as e:
            print(f"Erreur lors de la validation de l'item {item_id}: {str(e)}")
            return False
    
    def items_exist(self, item_ids):
        """Vérifie si plusieurs items existent dans la base de données"""
        if not item_ids:
            print("Aucun item à valider")
            return False
            
        try:
            # Vérifier les items dans la table purchases
            purchases_query = text("""
                SELECT item_id, COUNT(*) as count
                FROM purchases
                WHERE item_id IN :item_ids
                GROUP BY item_id
            """)
            purchases_results = {row[0]: row[1] for row in self.db.execute(purchases_query, {"item_ids": tuple(item_ids)})}
            
            # Vérifier les items dans la table sessions
            sessions_query = text("""
                SELECT item_id, COUNT(*) as count
                FROM sessions
                WHERE item_id IN :item_ids
                GROUP BY item_id
            """)
            sessions_results = {row[0]: row[1] for row in self.db.execute(sessions_query, {"item_ids": tuple(item_ids)})}
            
            # Vérifier chaque item
            found_items = set()
            for item_id in item_ids:
                purchases_count = purchases_results.get(item_id, 0)
                sessions_count = sessions_results.get(item_id, 0)
                if purchases_count > 0 or sessions_count > 0:
                    found_items.add(item_id)
                    print(f"Item {item_id}: Trouvé dans {purchases_count} achats et {sessions_count} sessions")
                else:
                    print(f"Item {item_id}: Non trouvé dans la base de données")
            
            all_exist = len(found_items) == len(item_ids)
            print(f"Validation des items: {len(found_items)}/{len(item_ids)} items trouvés")
            return all_exist
            
        except Exception as e:
            print(f"Erreur lors de la validation des items: {str(e)}")
            return False
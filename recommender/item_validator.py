from sqlalchemy.orm import Session
from sqlalchemy import text

class ItemValidator:
    def __init__(self, db: Session):
        self.db = db
    
    def item_exists(self, item_id):
        """Vérifie si un item existe dans la base de données"""
        try:
            # Optimisation: une seule requête avec UNION
            query = text("""
                SELECT COUNT(*) FROM (
                    SELECT item_id FROM purchases WHERE item_id = :item_id
                    UNION
                    SELECT item_id FROM sessions WHERE item_id = :item_id
                ) AS combined_items
            """)
            
            count = self.db.execute(query, {"item_id": item_id}).scalar()
            exists = count > 0
            
            if not exists:
                print(f"⚠️ L'item {item_id} n'existe pas dans la base de données")
            
            return exists
        except Exception as e:
            print(f"❌ Erreur lors de la validation de l'item {item_id}: {str(e)}")
            return False
    
    def items_exist(self, item_ids):
        """Vérifie si plusieurs items existent et renvoie ceux qui existent"""
        if not item_ids:
            print("⚠️ Aucun item à valider")
            return False, []
            
        try:
            # Requête optimisée pour récupérer les items valides en une opération
            query = text("""
                SELECT DISTINCT item_id 
                FROM (
                    SELECT item_id FROM purchases WHERE item_id IN :item_ids
                    UNION
                    SELECT item_id FROM sessions WHERE item_id IN :item_ids
                ) AS combined_items
            """)
            
            result = self.db.execute(query, {"item_ids": tuple(item_ids)})
            valid_items = [row[0] for row in result]
            
            missing_items = list(set(item_ids) - set(valid_items))
            if missing_items:
                print(f"⚠️ Les items suivants n'existent pas: {missing_items}")
            
            all_exist = len(valid_items) == len(item_ids)
            return all_exist, valid_items
            
        except Exception as e:
            print(f"❌ Erreur lors de la validation des items: {str(e)}")
            return False, []

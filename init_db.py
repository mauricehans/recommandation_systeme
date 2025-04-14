from sqlalchemy import create_engine, text

def init_database():
    # Création de la connexion à la base de données
    engine = create_engine('mysql://root:@localhost/recommandation_system')
    
    try:
        # Création des tables
        with engine.connect() as conn:
            # Suppression des données existantes
            conn.execute(text("DELETE FROM purchases"))
            conn.execute(text("DELETE FROM sessions"))
            
            # Création de la table purchases
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS purchases (
                    session_id INT,
                    item_id INT,
                    purchase_date DATETIME,
                    PRIMARY KEY (session_id, item_id)
                )
            """))
            
            # Création de la table sessions
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id INT,
                    item_id INT,
                    view_date DATETIME,
                    PRIMARY KEY (session_id, item_id, view_date)
                )
            """))
            
            # Insertion des données de test dans purchases
            conn.execute(text("""
                INSERT INTO purchases (session_id, item_id, purchase_date)
                VALUES 
                    (1, 1, NOW()),
                    (1, 2, NOW()),
                    (2, 2, NOW()),
                    (2, 3, NOW()),
                    (3, 1, NOW()),
                    (3, 3, NOW())
            """))
            
            # Insertion des données de test dans sessions
            conn.execute(text("""
                INSERT INTO sessions (session_id, item_id, view_date)
                VALUES 
                    (1, 1, NOW()),
                    (1, 2, NOW()),
                    (2, 2, NOW()),
                    (2, 3, NOW()),
                    (3, 1, NOW()),
                    (3, 3, NOW())
            """))
            
            # Pas besoin de commit() explicite avec execute()
            print("✅ Base de données initialisée avec succès !")
            
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation de la base de données : {str(e)}")

if __name__ == "__main__":
    init_database()
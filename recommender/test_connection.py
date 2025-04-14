from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
import pymysql

def test_database_connection():
    DATABASE_URL = "mysql://root:@localhost/recommandation_system"
    
    try:
        # Tentative de création du moteur de base de données
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        
        # Tentative de connexion
        with engine.connect() as connection:
            # Exécution d'une requête simple pour tester la connexion
            result = connection.execute("SELECT 1")
            print("✅ Connexion à la base de données réussie !")
            print("   - Serveur: localhost")
            print("   - Base de données: recommandation_system")
            print("   - Utilisateur: root")
            return True
            
    except SQLAlchemyError as e:
        print("❌ Erreur de connexion à la base de données :")
        print(f"   {str(e)}")
        return False

if __name__ == "__main__":
    test_database_connection()
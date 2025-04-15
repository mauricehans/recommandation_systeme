from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy import text
import pandas as pd
import random
from .models import Purchase, Session as SessionModel
from .item_validator import ItemValidator
from .recommender import ProductRecommender
import logging

logger = logging.getLogger(__name__)

class StatsAnalyzer:
    def __init__(self, db: Session):
        self.db = db
        self.validator = ItemValidator(db)
        self.recommender = ProductRecommender(db)

    def get_random_items(self, num_items=10):
        """Récupère des items aléatoires existants dans la base"""
        try:
            # Requête optimisée pour récupérer des items aléatoires
            query = text("""
                SELECT item_id FROM (
                    SELECT DISTINCT item_id FROM purchases
                    UNION
                    SELECT DISTINCT item_id FROM sessions
                ) AS combined_items
                ORDER BY RAND()
                LIMIT %s
            """)
            result = self.db.execute(query, (num_items,))
            return [row[0] for row in result]
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des items aléatoires: {str(e)}")
            return []

    def calculate_stats(self, item_ids):
        """Calcule les statistiques de recommandation"""
        try:
            # Importation des données jointes
            purchases_query = self.db.query(
                Purchase.session_id,
                Purchase.item_id,
                Purchase.purchase_date
            ).filter(Purchase.item_id.in_(item_ids))

            sessions_query = self.db.query(
                SessionModel.session_id,
                SessionModel.item_id,
                SessionModel.view_date
            ).filter(SessionModel.item_id.in_(item_ids))

            # Création des DataFrames
            purchases_df = pd.read_sql(purchases_query.statement, self.db.bind)
            sessions_df = pd.read_sql(sessions_query.statement, self.db.bind)

            # Fusion des données
            merged_df = pd.merge(
                sessions_df,
                purchases_df,
                on=['session_id', 'item_id'],
                how='left',
                suffixes=('_view', '_purchase')
            )

            # Calcul des métriques
            stats = merged_df.groupby('item_id').agg(
                total_views=('item_id', 'count'),
                total_purchases=('purchase_date', 'count'),
                view_to_purchase_rate=('purchase_date', lambda x: x.notna().mean())
            ).reset_index()

            # Ajout des recommandations
            recommendations = []
            for item_id in item_ids:
                recs = self.recommender.recommend_for_product(item_id)
                if recs:
                    recommendations.append({
                        'item_id': item_id,
                        'top_recommendation': recs[0]['item_id'],
                        'recommendation_score': recs[0]['score']
                    })

            recommendations_df = pd.DataFrame(recommendations)
            final_df = pd.merge(stats, recommendations_df, on='item_id', how='left')

            return final_df
        except Exception as e:
            logger.error(f"Erreur lors du calcul des statistiques: {str(e)}")
            return pd.DataFrame()

    def generate_report(self, num_items=10):
        """Génère un rapport complet"""
        items = self.get_random_items(num_items)
        if not items:
            return None

        stats_df = self.calculate_stats(items)
        if stats_df.empty:
            return None

        try:
            # Génération du CSV
            stats_df.to_csv('rapport_recommandations.csv', index=False, encoding='utf-8-sig')
            logger.info("Rapport généré avec succès: rapport_recommandations.csv")
            return stats_df
        except Exception as e:
            logger.error(f"Erreur lors de la génération du rapport: {str(e)}")
            return None

if __name__ == "__main__":
    from .database import SessionLocal
    db = SessionLocal()
    analyzer = StatsAnalyzer(db)
    report = analyzer.generate_report()
    if report is not None:
        print("Rapport généré avec succès!")
    else:
        print("Échec de la génération du rapport")
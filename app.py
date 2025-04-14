import streamlit as st
import pandas as pd
from recommender.recommender import ProductRecommender
from recommender.database import get_db

# Initialisation du système de recommandation avec la connexion à la base de données
db = next(get_db())
recommender = ProductRecommender(db=db)

# Configuration de la page Streamlit
st.set_page_config(
    page_title="Système de Recommandation de Produits",
    layout="wide"
)

# Titre principal
st.title("Système de Recommandation de Produits")

# Création de deux colonnes pour l'interface
col1, col2 = st.columns(2)

with col1:
    st.header("Recherche de Produits")
    
    # Sélection d'un produit unique
    product_id = st.number_input("Entrez l'ID du produit", min_value=1, value=1)
    
    if st.button("Obtenir les recommandations"):
        # Obtention des recommandations
        recommendations = recommender.get_frequently_bought_together(product_id)
        
        if recommendations:
            st.subheader("Produits fréquemment achetés ensemble")
            df = pd.DataFrame(recommendations)
            st.dataframe(df)
            
            # Création d'un graphique de score
            st.bar_chart(df.set_index('item_id')['score'])
        else:
            st.info("Aucune recommandation trouvée pour ce produit.")

with col2:
    st.header("Recommandations Multi-Produits")
    
    # Sélection multiple de produits
    product_ids_input = st.text_input(
        "Entrez plusieurs IDs de produits (séparés par des virgules)",
        "1,2,3"
    )
    
    if st.button("Obtenir les recommandations combinées"):
        try:
            # Conversion de l'entrée en liste d'entiers
            product_ids = [int(id.strip()) for id in product_ids_input.split(',')]
            
            # Obtention des recommandations pour plusieurs produits
            multi_recommendations = recommender.recommend_for_products(product_ids)
            
            if multi_recommendations:
                st.subheader("Recommandations basées sur plusieurs produits")
                df_multi = pd.DataFrame(multi_recommendations)
                st.dataframe(df_multi)
                
                # Création d'un graphique de score
                st.bar_chart(df_multi.set_index('item_id')['score'])
            else:
                st.info("Aucune recommandation trouvée pour cette combinaison de produits.")
        except ValueError:
            st.error("Veuillez entrer des IDs de produits valides.")

# Affichage des informations sur le système
st.sidebar.title("À propos")
st.sidebar.info("""
    Ce système de recommandation utilise l'historique des achats pour suggérer des produits
    pertinents basés sur les comportements d'achat des utilisateurs.
    
    Les recommandations sont calculées en utilisant :
    - Les produits fréquemment achetés ensemble
    - Les tendances d'achat des 30 derniers jours
""")

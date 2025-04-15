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

# Onglets pour séparer les fonctionnalités
tab1, tab2, tab3 = st.tabs(["Produit Unique", "Multi-Produits", "Parcours d'Achat"])

with tab1:
    st.header("Recommandations pour un produit")
    
    # Sélection d'un produit unique
    product_id = st.number_input("Entrez l'ID du produit", min_value=1, value=1, key="single_product")
    num_recs = st.slider("Nombre de recommandations", min_value=1, max_value=10, value=5, step=1)
    
    if st.button("Obtenir les recommandations", key="btn_single"):
        # Validation de l'item
        if recommender.validator.item_exists(product_id):
            # Obtention des recommandations
            recommendations = recommender.recommend_for_product(product_id, num_recommendations=num_recs)
            
            if recommendations:
                st.success(f"✅ {len(recommendations)} recommandations trouvées")
                df = pd.DataFrame(recommendations)
                st.dataframe(df)
                
                # Création d'un graphique de score
                st.bar_chart(df.set_index('item_id')['score'])
            else:
                st.info("Aucune recommandation trouvée pour ce produit.")
        else:
            st.error(f"⚠️ Le produit avec ID {product_id} n'existe pas dans la base de données.")

with tab2:
    st.header("Recommandations Multi-Produits")
    
    # Sélection multiple de produits
    product_ids_input = st.text_input(
        "Entrez plusieurs IDs de produits (séparés par des virgules)",
        "1,2,3",
        key="multi_products"
    )
    num_multi_recs = st.slider("Nombre de recommandations", min_value=1, max_value=10, value=5, step=1, key="slider_multi")
    
    if st.button("Obtenir les recommandations combinées", key="btn_multi"):
        try:
            # Conversion de l'entrée en liste d'entiers
            product_ids = [int(id.strip()) for id in product_ids_input.split(',')]
            
            # Validation des IDs
            all_exist, valid_ids = recommender.validator.items_exist(product_ids)
            if not all_exist:
                invalid_ids = set(product_ids) - set(valid_ids)
                st.warning(f"⚠️ Les produits suivants n'existent pas dans la base de données: {invalid_ids}")
                st.info(f"Seuls les produits valides seront utilisés: {valid_ids}")
            
            if valid_ids:
                # Obtention des recommandations pour les produits valides
                multi_recommendations = recommender.recommend_for_products(valid_ids, num_recommendations=num_multi_recs)
                
                if multi_recommendations:
                    st.success(f"✅ {len(multi_recommendations)} recommandations trouvées")
                    df_multi = pd.DataFrame(multi_recommendations)
                    st.dataframe(df_multi)
                    
                    # Création d'un graphique de score
                    st.bar_chart(df_multi.set_index('item_id')['score'])
                else:
                    st.info("Aucune recommandation trouvée pour cette combinaison de produits.")
            else:
                st.error("Aucun ID de produit valide fourni.")
        except ValueError:
            st.error("⚠️ Veuillez entrer des IDs de produits valides (nombres entiers séparés par des virgules).")

with tab3:
    st.header("Analyse des Parcours d'Achat")
    
    # Sélection d'un produit pour l'analyse de parcours
    path_product_id = st.number_input("Entrez l'ID du produit", min_value=1, value=1, key="path_product")
    max_path_length = st.slider("Longueur maximale du parcours", min_value=2, max_value=10, value=5)
    min_support = st.slider("Support minimum (fréquence)", min_value=1, max_value=10, value=2)
    
    if st.button("Analyser les parcours d'achat", key="btn_path"):
        # Validation de l'item
        if recommender.validator.item_exists(path_product_id):
            # Obtention des parcours d'achat
            paths = recommender.get_purchase_paths(
                path_product_id, 
                max_path_length=max_path_length,
                min_support=min_support
            )
            
            if paths:
                st.success(f"✅ {len(paths)} parcours d'achat identifiés")
                
                # Affichage des parcours sous forme de tableau
                paths_display = []
                for p in paths:
                    paths_display.append({
                        "Parcours": " → ".join(map(str, p["path"])),
                        "Fréquence": p["frequency"]
                    })
                
                st.dataframe(pd.DataFrame(paths_display))
                
                # Visualisation des fréquences
                df_paths = pd.DataFrame([(str(i+1), p["frequency"]) for i, p in enumerate(paths)], 
                                     columns=["Parcours", "Fréquence"])
                st.bar_chart(df_paths.set_index("Parcours"))
            else:
                st.info("Aucun parcours d'achat identifié pour ce produit avec les critères spécifiés.")
        else:
            st.error(f"⚠️ Le produit avec ID {path_product_id} n'existe pas dans la base de données.")

# Informations dans la barre latérale
st.sidebar.title("À propos")
st.sidebar.info("""
    Ce système de recommandation utilise l'historique des achats et des consultations pour suggérer des produits
    pertinents basés sur les comportements des utilisateurs.
    
    Méthodes de recommandation :
    - Produits fréquemment achetés ensemble
    - Séquences de consultation-achat
    - Analyse de parcours d'achat
""")

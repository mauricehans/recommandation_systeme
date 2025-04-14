from flask import Flask, request, jsonify
from recommender.database import engine, get_db, Base
from recommender.models import User, Product, Interaction
from recommender.recommender import RecommendationSystem
from sqlalchemy.orm import Session

app = Flask(__name__)

# Créer les tables dans la base de données
Base.metadata.create_all(bind=engine)

@app.route('/recommendations/<int:user_id>', methods=['GET'])
def get_recommendations(user_id):
    db = next(get_db())
    recommender = RecommendationSystem(db)
    num_recs = request.args.get('num', default=5, type=int)
    recommendations = recommender.recommend_for_user(user_id, num_recommendations=num_recs)
    return jsonify(recommendations)

@app.route('/users', methods=['POST'])
def create_user():
    data = request.json
    db = next(get_db())
    user = User(username=data['username'])
    db.add(user)
    db.commit()
    db.refresh(user)
    return jsonify({"id": user.id, "username": user.username})

@app.route('/products', methods=['POST'])
def create_product():
    data = request.json
    db = next(get_db())
    product = Product(name=data['name'], category=data['category'])
    db.add(product)
    db.commit()
    db.refresh(product)
    return jsonify({"id": product.id, "name": product.name, "category": product.category})

@app.route('/interactions', methods=['POST'])
def create_interaction():
    data = request.json
    db = next(get_db())
    interaction = Interaction(
        user_id=data['user_id'],
        product_id=data['product_id'],
        rating=data['rating']
    )
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    return jsonify({"id": interaction.id, "user_id": interaction.user_id, 
                   "product_id": interaction.product_id, "rating": interaction.rating})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)

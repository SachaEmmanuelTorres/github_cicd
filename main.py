"""
Application Flask simple avec requests
Structure pour projet uv
"""

import os
import requests
from flask import Flask, jsonify, request
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

app = Flask(__name__)

# Configuration
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
app.config["DEBUG"] = os.getenv("FLASK_ENV") == "development"


@app.route("/")
def home():
    """Page d'accueil simple"""
    return jsonify(
        {
            "message": "Bienvenue dans mon app Flask!",
            "version": "1.0.0",
            "status": "running",
        }
    )


@app.route("/health")
def health_check():
    """Endpoint de santé pour le monitoring"""
    return jsonify({"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}), 200


@app.route("/users")
def get_users():
    """Récupère des utilisateurs depuis une API externe"""
    try:
        # Utilisation de requests pour appeler une API externe
        response = requests.get("https://jsonplaceholder.typicode.com/users", timeout=5)
        response.raise_for_status()

        users = response.json()
        # Simplifier les données utilisateur
        simplified_users = [
            {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "city": user["address"]["city"],
            }
            for user in users[:5]  # Limiter à 5 utilisateurs
        ]

        return jsonify({"users": simplified_users, "count": len(simplified_users)})

    except requests.RequestException as e:
        return (
            jsonify(
                {"error": "Impossible de récupérer les utilisateurs", "details": str(e)}
            ),
            500,
        )


@app.route("/users/<int:user_id>")
def get_user(user_id):
    """Récupère un utilisateur spécifique"""
    try:
        response = requests.get(
            f"https://jsonplaceholder.typicode.com/users/{user_id}", timeout=5
        )

        if response.status_code == 404:
            return jsonify({"error": "Utilisateur non trouvé"}), 404

        response.raise_for_status()
        user = response.json()

        return jsonify(
            {
                "user": {
                    "id": user["id"],
                    "name": user["name"],
                    "email": user["email"],
                    "phone": user["phone"],
                    "website": user["website"],
                }
            }
        )

    except requests.RequestException as e:
        return (
            jsonify(
                {
                    "error": "Erreur lors de la récupération de l'utilisateur",
                    "details": str(e),
                }
            ),
            500,
        )


@app.route("/calc/add", methods=["POST"])
def add_numbers():
    """Endpoint pour additionner deux nombres"""
    try:
        data = request.get_json()

        if not data or "a" not in data or "b" not in data:
            return jsonify({"error": "Paramètres 'a' et 'b' requis"}), 400

        a = float(data["a"])
        b = float(data["b"])
        result = a + b

        return jsonify({"operation": "addition", "a": a, "b": b, "result": result})

    except (ValueError, TypeError) as e:
        return (
            jsonify(
                {"error": "Les paramètres doivent être des nombres", "details": str(e)}
            ),
            400,
        )


@app.errorhandler(404)
def not_found(error):
    """Gestionnaire d'erreur 404"""
    return (
        jsonify(
            {"error": "Endpoint non trouvé", "message": "L'URL demandée n'existe pas"}
        ),
        404,
    )


@app.errorhandler(500)
def internal_error(error):
    """Gestionnaire d'erreur 500"""
    return (
        jsonify(
            {
                "error": "Erreur interne du serveur",
                "message": "Une erreur inattendue s'est produite",
            }
        ),
        500,
    )


def create_app():
    """Factory function pour créer l'app (utile pour les tests)"""
    return app


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=app.config["DEBUG"])

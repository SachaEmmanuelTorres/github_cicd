"""
Tests pour l'application Flask main.py
Structure pour projet uv avec pytest
"""

import json
import pytest
import responses
from unittest.mock import patch
from ..main import app, create_app


@pytest.fixture
def client():
    """Fixture pour le client de test Flask"""
    app.config["TESTING"] = True
    app.config["DEBUG"] = False

    with app.test_client() as client:
        with app.app_context():
            yield client


@pytest.fixture
def sample_user_data():
    """Données utilisateur pour les tests"""
    return {
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "123-456-7890",
        "website": "johndoe.com",
        "address": {"city": "Paris"},
    }


@pytest.fixture
def sample_users_data():
    """Liste d'utilisateurs pour les tests"""
    return [
        {
            "id": 1,
            "name": "John Doe",
            "email": "john@example.com",
            "address": {"city": "Paris"},
        },
        {
            "id": 2,
            "name": "Jane Smith",
            "email": "jane@example.com",
            "address": {"city": "Lyon"},
        },
    ]


class TestHomeEndpoint:
    """Tests pour l'endpoint d'accueil"""

    def test_home_returns_welcome_message(self, client):
        """Test que la page d'accueil retourne le bon message"""
        response = client.get("/")

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["message"] == "Bienvenue dans mon app Flask!"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"


class TestHealthCheck:
    """Tests pour l'endpoint de santé"""

    def test_health_check_returns_healthy_status(self, client):
        """Test que le health check retourne un statut healthy"""
        response = client.get("/health")

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["status"] == "healthy"
        assert "timestamp" in data


class TestUsersEndpoint:
    """Tests pour les endpoints utilisateurs"""

    @responses.activate
    def test_get_users_success(self, client, sample_users_data):
        """Test récupération des utilisateurs avec succès"""
        # Mock de l'API externe
        responses.add(
            responses.GET,
            "https://jsonplaceholder.typicode.com/users",
            json=sample_users_data,
            status=200,
        )

        response = client.get("/users")

        assert response.status_code == 200
        data = json.loads(response.data)

        assert "users" in data
        assert "count" in data
        assert data["count"] == 2
        assert len(data["users"]) == 2

        # Vérifier la structure des données utilisateur
        user = data["users"][0]
        assert "id" in user
        assert "name" in user
        assert "email" in user
        assert "city" in user

    @responses.activate
    def test_get_users_api_error(self, client):
        """Test gestion d'erreur lors de l'appel API externe"""
        # Mock d'une erreur API
        responses.add(
            responses.GET, "https://jsonplaceholder.typicode.com/users", status=500
        )

        response = client.get("/users")

        assert response.status_code == 500
        data = json.loads(response.data)

        assert "error" in data
        assert data["error"] == "Impossible de récupérer les utilisateurs"

    @responses.activate
    def test_get_user_by_id_success(self, client, sample_user_data):
        """Test récupération d'un utilisateur spécifique"""
        user_id = 1
        responses.add(
            responses.GET,
            f"https://jsonplaceholder.typicode.com/users/{user_id}",
            json=sample_user_data,
            status=200,
        )

        response = client.get(f"/users/{user_id}")

        assert response.status_code == 200
        data = json.loads(response.data)

        assert "user" in data
        user = data["user"]
        assert user["id"] == 1
        assert user["name"] == "John Doe"
        assert user["email"] == "john@example.com"

    @responses.activate
    def test_get_user_not_found(self, client):
        """Test utilisateur non trouvé"""
        user_id = 999
        responses.add(
            responses.GET,
            f"https://jsonplaceholder.typicode.com/users/{user_id}",
            status=404,
        )

        response = client.get(f"/users/{user_id}")

        assert response.status_code == 404
        data = json.loads(response.data)

        assert data["error"] == "Utilisateur non trouvé"


class TestCalculatorEndpoint:
    """Tests pour l'endpoint de calcul"""

    def test_add_numbers_success(self, client):
        """Test addition de deux nombres"""
        payload = {"a": 5, "b": 3}

        response = client.post(
            "/calc/add", data=json.dumps(payload), content_type="application/json"
        )

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["operation"] == "addition"
        assert data["a"] == 5
        assert data["b"] == 3
        assert data["result"] == 8

    def test_add_numbers_with_floats(self, client):
        """Test addition avec des nombres décimaux"""
        payload = {"a": 2.5, "b": 1.5}

        response = client.post(
            "/calc/add", data=json.dumps(payload), content_type="application/json"
        )

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["result"] == 4.0

    def test_add_numbers_missing_parameters(self, client):
        """Test avec paramètres manquants"""
        payload = {"a": 5}  # Manque 'b'

        response = client.post(
            "/calc/add", data=json.dumps(payload), content_type="application/json"
        )

        assert response.status_code == 400
        data = json.loads(response.data)

        assert "Paramètres 'a' et 'b' requis" in data["error"]

    def test_add_numbers_invalid_types(self, client):
        """Test avec types invalides"""
        payload = {"a": "not_a_number", "b": 3}

        response = client.post(
            "/calc/add", data=json.dumps(payload), content_type="application/json"
        )

        assert response.status_code == 400
        data = json.loads(response.data)

        assert "Les paramètres doivent être des nombres" in data["error"]

    def test_add_numbers_no_json(self, client):
        """Test sans données JSON"""
        response = client.post("/calc/add")

        assert response.status_code == 400


class TestErrorHandlers:
    """Tests pour les gestionnaires d'erreur"""

    def test_404_error_handler(self, client):
        """Test gestionnaire d'erreur 404"""
        response = client.get("/endpoint-inexistant")

        assert response.status_code == 404
        data = json.loads(response.data)

        assert data["error"] == "Endpoint non trouvé"
        assert "L'URL demandée n'existe pas" in data["message"]


class TestAppFactory:
    """Tests pour la factory function"""

    def test_create_app_returns_flask_app(self):
        """Test que create_app retourne une instance Flask"""
        app_instance = create_app()

        assert app_instance is not None
        assert hasattr(app_instance, "test_client")


class TestIntegration:
    """Tests d'intégration"""

    @responses.activate
    def test_full_user_workflow(self, client, sample_users_data, sample_user_data):
        """Test complet du workflow utilisateur"""
        # Mock pour la liste des utilisateurs
        responses.add(
            responses.GET,
            "https://jsonplaceholder.typicode.com/users",
            json=sample_users_data,
            status=200,
        )

        # Mock pour un utilisateur spécifique
        responses.add(
            responses.GET,
            "https://jsonplaceholder.typicode.com/users/1",
            json=sample_user_data,
            status=200,
        )

        # 1. Vérifier que l'app fonctionne
        health_response = client.get("/health")
        assert health_response.status_code == 200

        # 2. Récupérer la liste des utilisateurs
        users_response = client.get("/users")
        assert users_response.status_code == 200
        users_data = json.loads(users_response.data)
        assert users_data["count"] > 0

        # 3. Récupérer un utilisateur spécifique
        user_response = client.get("/users/1")
        assert user_response.status_code == 200
        user_data = json.loads(user_response.data)
        assert user_data["user"]["id"] == 1

        # 4. Faire un calcul
        calc_response = client.post(
            "/calc/add",
            data=json.dumps({"a": 10, "b": 5}),
            content_type="application/json",
        )
        assert calc_response.status_code == 200
        calc_data = json.loads(calc_response.data)
        assert calc_data["result"] == 15


# Tests de performance (optionnel)
class TestPerformance:
    """Tests de performance basiques"""

    def test_home_endpoint_response_time(self, client):
        """Test que l'endpoint d'accueil répond rapidement"""
        import time

        start_time = time.time()
        response = client.get("/")
        end_time = time.time()

        response_time = end_time - start_time

        assert response.status_code == 200
        assert response_time < 0.1  # Moins de 100ms

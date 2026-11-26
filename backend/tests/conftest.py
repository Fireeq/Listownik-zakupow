import pytest

from app import create_app


@pytest.fixture
def database_path(tmp_path):
    return tmp_path / "listownik-test.db"


@pytest.fixture
def app(database_path):
    return create_app({"DATABASE": str(database_path), "TESTING": True})


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def make_list(client):
    def create_shopping_list(name="Zakupy na weekend"):
        response = client.post("/api/lists", json={"name": name})
        assert response.status_code == 201
        return response.get_json()

    return create_shopping_list


@pytest.fixture
def make_item(client):
    def create_list_item(list_id, name="Mleko", quantity=1):
        response = client.post(
            f"/api/lists/{list_id}/items", json={"name": name, "quantity": quantity}
        )
        assert response.status_code == 201
        return response.get_json()

    return create_list_item


@pytest.fixture
def mark_purchased(client):
    def set_purchased(list_id, item_id):
        response = client.patch(
            f"/api/lists/{list_id}/items/{item_id}", json={"is_purchased": True}
        )
        assert response.status_code == 200
        return response.get_json()

    return set_purchased

import sqlite3
from contextlib import closing

from app import create_app


def count_items_in_database(database_path, list_id):
    with closing(sqlite3.connect(database_path)) as connection:
        query = "SELECT COUNT(*) FROM items WHERE list_id = ?"
        return connection.execute(query, (list_id,)).fetchone()[0]


def test_create_list_returns_created_list_with_trimmed_name(client):
    # Arrange
    payload = {"name": "  Zakupy na weekend  "}

    # Act
    response = client.post("/api/lists", json=payload)

    # Assert
    assert response.status_code == 201
    assert response.get_json() == {"id": 1, "name": "Zakupy na weekend"}


def test_get_lists_returns_newest_first_with_item_counts(
    client, make_list, make_item, mark_purchased
):
    # Arrange
    grocery_list = make_list("Biedronka")
    drugstore_list = make_list("Drogeria")
    milk = make_item(grocery_list["id"], "Mleko", 2)
    make_item(grocery_list["id"], "Chleb", 1)
    mark_purchased(grocery_list["id"], milk["id"])

    # Act
    response = client.get("/api/lists")

    # Assert
    assert response.status_code == 200
    assert response.get_json() == [
        {"id": drugstore_list["id"], "name": "Drogeria", "total_count": 0, "purchased_count": 0},
        {"id": grocery_list["id"], "name": "Biedronka", "total_count": 2, "purchased_count": 1},
    ]


def test_rename_list_changes_its_name(client, make_list):
    # Arrange
    shopping_list = make_list("Zakupy na weekend")

    # Act
    response = client.patch(
        f"/api/lists/{shopping_list['id']}", json={"name": "Zakupy na poniedziałek"}
    )

    # Assert
    assert response.status_code == 200
    assert response.get_json() == {"id": shopping_list["id"], "name": "Zakupy na poniedziałek"}
    saved_list = client.get(f"/api/lists/{shopping_list['id']}").get_json()
    assert saved_list["name"] == "Zakupy na poniedziałek"


def test_delete_list_removes_list_together_with_its_items(
    client, make_list, make_item, database_path
):
    # Arrange
    shopping_list = make_list("Biedronka")
    make_item(shopping_list["id"], "Mleko", 2)
    make_item(shopping_list["id"], "Chleb", 1)

    # Act
    response = client.delete(f"/api/lists/{shopping_list['id']}")

    # Assert
    assert response.status_code == 204
    assert client.get(f"/api/lists/{shopping_list['id']}").status_code == 404
    assert count_items_in_database(database_path, shopping_list["id"]) == 0


def test_create_list_with_blank_name_returns_validation_error(client):
    # Arrange
    payload = {"name": "   "}

    # Act
    response = client.post("/api/lists", json=payload)

    # Assert
    assert response.status_code == 400
    assert response.get_json() == {"error": "Nazwa nie może być pusta."}
    assert client.get("/api/lists").get_json() == []


def test_saved_list_is_available_after_application_restart(database_path):
    # Arrange
    first_client = create_app({"DATABASE": str(database_path), "TESTING": True}).test_client()
    first_client.post("/api/lists", json={"name": "Lista po restarcie"})

    # Act
    restarted_client = create_app({"DATABASE": str(database_path), "TESTING": True}).test_client()
    response = restarted_client.get("/api/lists")

    # Assert
    assert [shopping_list["name"] for shopping_list in response.get_json()] == [
        "Lista po restarcie"
    ]

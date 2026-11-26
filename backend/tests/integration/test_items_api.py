def item_url(list_id, item_id):
    return f"/api/lists/{list_id}/items/{item_id}"


def test_create_item_returns_new_item_marked_as_not_purchased(client, make_list):
    # Arrange
    shopping_list = make_list()
    payload = {"name": "Mleko", "quantity": 2}

    # Act
    response = client.post(f"/api/lists/{shopping_list['id']}/items", json=payload)

    # Assert
    assert response.status_code == 201
    assert response.get_json() == {"id": 1, "name": "Mleko", "quantity": 2, "is_purchased": False}


def test_create_item_for_missing_list_returns_not_found(client):
    # Arrange
    payload = {"name": "Mleko", "quantity": 1}

    # Act
    response = client.post("/api/lists/999/items", json=payload)

    # Assert
    assert response.status_code == 404
    assert response.get_json() == {"error": "Nie znaleziono wskazanej listy, produktu lub adresu."}


def test_update_item_changes_only_sent_fields(client, make_list, make_item):
    # Arrange
    shopping_list = make_list()
    item = make_item(shopping_list["id"], "Mleko", 2)

    # Act
    response = client.patch(item_url(shopping_list["id"], item["id"]), json={"name": "Mleko 2%"})

    # Assert
    assert response.status_code == 200
    assert response.get_json() == {
        "id": item["id"],
        "name": "Mleko 2%",
        "quantity": 2,
        "is_purchased": False,
    }


def test_update_item_marks_item_as_purchased(client, make_list, make_item):
    # Arrange
    shopping_list = make_list()
    item = make_item(shopping_list["id"])

    # Act
    response = client.patch(
        item_url(shopping_list["id"], item["id"]), json={"is_purchased": True}
    )

    # Assert
    assert response.status_code == 200
    assert response.get_json()["is_purchased"] is True
    summary = client.get("/api/lists").get_json()[0]
    assert (summary["total_count"], summary["purchased_count"]) == (1, 1)


def test_update_item_through_another_list_returns_not_found(client, make_list, make_item):
    # Arrange
    grocery_list = make_list("Biedronka")
    drugstore_list = make_list("Drogeria")
    item = make_item(grocery_list["id"], "Mleko", 2)

    # Act
    response = client.patch(item_url(drugstore_list["id"], item["id"]), json={"quantity": 5})

    # Assert
    assert response.status_code == 404
    saved_items = client.get(f"/api/lists/{grocery_list['id']}").get_json()["items"]
    assert saved_items[0]["quantity"] == 2


def test_delete_item_removes_only_selected_item(client, make_list, make_item):
    # Arrange
    shopping_list = make_list()
    milk = make_item(shopping_list["id"], "Mleko", 2)
    bread = make_item(shopping_list["id"], "Chleb", 1)

    # Act
    response = client.delete(item_url(shopping_list["id"], milk["id"]))

    # Assert
    assert response.status_code == 204
    remaining_items = client.get(f"/api/lists/{shopping_list['id']}").get_json()["items"]
    assert [item["id"] for item in remaining_items] == [bread["id"]]

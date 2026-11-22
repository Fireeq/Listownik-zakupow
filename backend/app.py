from pathlib import Path
from sqlite3 import Row

from flask import Blueprint, Flask, abort, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from database import get_db, init_db
from validation import (
    ValidationError,
    validate_fields,
    validate_name,
    validate_purchased,
    validate_quantity,
)

api = Blueprint("api", __name__, url_prefix="/api")


def get_list(list_id: int) -> Row:
    row = get_db().execute(
        "SELECT id, name FROM shopping_lists WHERE id = ?", (list_id,)
    ).fetchone()
    if row is None:
        abort(404)
    return row


def get_item(list_id: int, item_id: int) -> dict:
    row = get_db().execute(
        "SELECT id, name, quantity, is_purchased FROM items WHERE list_id = ? AND id = ?",
        (list_id, item_id),
    ).fetchone()
    if row is None:
        abort(404)
    return serialize_item(row)


def serialize_item(row: Row) -> dict:
    return {**dict(row), "is_purchased": bool(row["is_purchased"])}


@api.get("/lists")
def list_shopping_lists():
    rows = get_db().execute(
        """
        SELECT shopping_lists.id, shopping_lists.name,
               COUNT(items.id) AS total_count,
               COALESCE(SUM(items.is_purchased), 0) AS purchased_count
        FROM shopping_lists
        LEFT JOIN items ON items.list_id = shopping_lists.id
        GROUP BY shopping_lists.id
        ORDER BY shopping_lists.id DESC
        """
    ).fetchall()
    return jsonify([dict(row) for row in rows])


@api.post("/lists")
def create_list():
    data = validate_fields(request.get_json(), {"name"})
    name = validate_name(data["name"])
    connection = get_db()
    with connection:
        cursor = connection.execute(
            "INSERT INTO shopping_lists (name) VALUES (?)", (name,)
        )
    return jsonify({"id": cursor.lastrowid, "name": name}), 201


@api.get("/lists/<int:list_id>")
def read_list(list_id: int):
    shopping_list = dict(get_list(list_id))
    rows = get_db().execute(
        """
        SELECT id, name, quantity, is_purchased FROM items
        WHERE list_id = ? ORDER BY is_purchased, id
        """,
        (list_id,),
    ).fetchall()
    return jsonify({**shopping_list, "items": [serialize_item(row) for row in rows]})


@api.patch("/lists/<int:list_id>")
def rename_list(list_id: int):
    data = validate_fields(request.get_json(), {"name"})
    name = validate_name(data["name"])
    connection = get_db()
    with connection:
        cursor = connection.execute(
            "UPDATE shopping_lists SET name = ? WHERE id = ?", (name, list_id)
        )
        if cursor.rowcount == 0:
            abort(404)
    return jsonify({"id": list_id, "name": name})


@api.delete("/lists/<int:list_id>")
def delete_list(list_id: int):
    connection = get_db()
    with connection:
        cursor = connection.execute("DELETE FROM shopping_lists WHERE id = ?", (list_id,))
        if cursor.rowcount == 0:
            abort(404)
    return "", 204


@api.post("/lists/<int:list_id>/items")
def create_item(list_id: int):
    data = validate_fields(request.get_json(), {"name", "quantity"})
    name = validate_name(data["name"])
    quantity = validate_quantity(data["quantity"])
    get_list(list_id)
    connection = get_db()
    with connection:
        cursor = connection.execute(
            "INSERT INTO items (list_id, name, quantity) VALUES (?, ?, ?)",
            (list_id, name, quantity),
        )
        item = get_item(list_id, cursor.lastrowid)
    return jsonify(item), 201


@api.patch("/lists/<int:list_id>/items/<int:item_id>")
def update_item(list_id: int, item_id: int):
    data = validate_fields(request.get_json(), set(), {"name", "quantity", "is_purchased"})
    name = validate_name(data["name"]) if "name" in data else None
    quantity = validate_quantity(data["quantity"]) if "quantity" in data else None
    purchased = validate_purchased(data["is_purchased"]) if "is_purchased" in data else None
    connection = get_db()
    with connection:
        cursor = connection.execute(
            """
            UPDATE items SET name = COALESCE(?, name), quantity = COALESCE(?, quantity),
                             is_purchased = COALESCE(?, is_purchased)
            WHERE list_id = ? AND id = ?
            """,
            (name, quantity, purchased, list_id, item_id),
        )
        if cursor.rowcount == 0:
            abort(404)
        item = get_item(list_id, item_id)
    return jsonify(item)


@api.delete("/lists/<int:list_id>/items/<int:item_id>")
def delete_item(list_id: int, item_id: int):
    connection = get_db()
    with connection:
        cursor = connection.execute(
            "DELETE FROM items WHERE list_id = ? AND id = ?", (list_id, item_id)
        )
        if cursor.rowcount == 0:
            abort(404)
    return "", 204


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE=str(Path(__file__).with_name("listownik.db")),
        MAX_CONTENT_LENGTH=16 * 1024,
    )
    if config is not None:
        app.config.update(config)
    app.json.ensure_ascii = False
    CORS(
        app,
        resources={r"/api/*": {"origins": ["http://127.0.0.1:5500", "http://localhost:5500"]}},
        methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type"],
        always_send=False,
    )
    app.register_blueprint(api)
    app.register_error_handler(ValidationError, handle_validation_error)
    app.register_error_handler(HTTPException, handle_http_error)
    init_db(app)
    return app


def handle_validation_error(error: ValidationError):
    return jsonify({"error": str(error)}), 400


def handle_http_error(error: HTTPException):
    messages = {
        400: "Prześlij poprawne dane JSON.",
        404: "Nie znaleziono wskazanej listy, produktu lub adresu.",
        405: "Ta metoda HTTP nie jest obsługiwana.",
        413: "Przesłane dane są zbyt duże.",
        415: "Prześlij dane w formacie JSON.",
    }
    response = error.get_response()
    response.set_data(
        jsonify({"error": messages.get(error.code, "Wystąpił błąd serwera.")}).get_data()
    )
    response.content_type = "application/json"
    return response


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000)

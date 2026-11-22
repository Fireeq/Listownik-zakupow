import sqlite3

from flask import Flask, current_app, g


def get_db() -> sqlite3.Connection:
    if "database" not in g:
        connection = sqlite3.connect(current_app.config["DATABASE"])
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        g.database = connection
    return g.database


def close_db(error: BaseException | None = None) -> None:
    connection = g.pop("database", None)
    if connection is not None:
        connection.close()


def init_db(app: Flask) -> None:
    app.teardown_appcontext(close_db)
    with app.app_context():
        get_db().executescript(
            """
            CREATE TABLE IF NOT EXISTS shopping_lists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL CHECK (length(trim(name)) BETWEEN 1 AND 80)
            );

            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                list_id INTEGER NOT NULL REFERENCES shopping_lists(id) ON DELETE CASCADE,
                name TEXT NOT NULL CHECK (length(trim(name)) BETWEEN 1 AND 80),
                quantity INTEGER NOT NULL CHECK (
                    typeof(quantity) = 'integer' AND quantity BETWEEN 1 AND 999
                ),
                is_purchased INTEGER NOT NULL DEFAULT 0 CHECK (is_purchased IN (0, 1))
            );

            CREATE INDEX IF NOT EXISTS items_list_id ON items(list_id);
            """
        )

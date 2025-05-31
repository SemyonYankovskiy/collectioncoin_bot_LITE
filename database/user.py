from datetime import datetime
from typing import Optional

from .database import db_connection as db, user_default_color_schema


class User:
    def __init__(
        self,
        tg_id: int,
        user_coin_id: str,
        user_name: Optional[str] = None,
        map_color_schema: Optional[str] = None,
        last_refresh: Optional[str] = None,
        show_pictures: Optional[bool] = False,
    ):
        self.tg_id = tg_id
        self.user_coin_id = user_coin_id
        self.user_name = user_name
        self.map_color_schema = map_color_schema or user_default_color_schema
        self.last_refresh = last_refresh
        self.show_pictures = bool(show_pictures)

    def save(self):
        try:
            db.cursor.execute(
                """
                INSERT INTO users (tg_id, user_coin_id, user_name, map_color_schema, last_refresh, show_pictures)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    self.tg_id,
                    self.user_coin_id,
                    self.user_name,
                    self.map_color_schema,
                    self.last_refresh,
                    int(self.show_pictures),
                ),
            )
            db.conn.commit()
            print(datetime.now(), "|", f"User {self.tg_id} added successfully!")
        except db.conn.IntegrityError:
            db.cursor.execute(
                """
                UPDATE users SET
                    user_coin_id = ?,
                    user_name = ?,
                    map_color_schema = ?,
                    last_refresh = ?,
                    show_pictures = ?
                WHERE tg_id = ?
                """,
                (
                    self.user_coin_id,
                    self.user_name,
                    self.map_color_schema,
                    self.last_refresh,
                    int(self.show_pictures),
                    self.tg_id,
                ),
            )
            db.conn.commit()
            print(datetime.now(), "|", f"User {self.tg_id} updated successfully!")

    @staticmethod
    def get(tg_id: int) -> Optional["User"]:
        db.cursor.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,))
        row = db.cursor.fetchone()
        return User(*row) if row else None

    @staticmethod
    def get_all():
        db.cursor.execute("SELECT * FROM users")
        return [User(*row) for row in db.cursor.fetchall()]

    @staticmethod
    def delete(tg_id: int):
        db.cursor.execute("DELETE FROM users WHERE tg_id = ?", (tg_id,))
        db.conn.commit()
        print(datetime.now(), "|", f"User {tg_id} removed successfully!")

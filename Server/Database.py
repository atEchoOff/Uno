from flask_sqlalchemy import SQLAlchemy
from typing import List
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, PickleType
from sqlalchemy.ext.mutable import MutableList

class Base(DeclarativeBase):
  pass

db = SQLAlchemy(model_class=Base)

class Room(db.Model):
    __tablename__ = "room_table"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    players: Mapped[List["RoomPlayer"]] = relationship(back_populates="room")

    # Current turn of the game
    # Incriments when someone plays, and to determine the current player, we do turn % len(players)
    # Also used to determine the current step in the broadcast queue
    turn: Mapped[int] = mapped_column(nullable=False, default=0)

    # Saves the current card to make sure users dont lie about the validity of the card they play
    current_card: Mapped[str] = mapped_column(nullable=True)

    # Whether or not the game is in session
    active: Mapped[bool] = mapped_column(nullable=False, default=False)

    # Save the total set of instructions in the game
    instruction_set = mapped_column(MutableList.as_mutable(PickleType), nullable=False, default=[])

class RoomPlayer(db.Model):
    __tablename__ = "player_table"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Save the user's name (for this game)
    name: Mapped[str] = mapped_column(nullable=False)

    # Save the user's deck
    deck = mapped_column(MutableList.as_mutable(PickleType), nullable=False)

    # Saves the turn according to the client
    turn: Mapped[int] = mapped_column(nullable=False, default=0)

    room_id = mapped_column(ForeignKey("room_table.id"))
    room: Mapped["Room"] = relationship(back_populates="players")

def init_db(app):
    db.init_app(app)

    with app.app_context():
        db.drop_all()
        db.create_all()
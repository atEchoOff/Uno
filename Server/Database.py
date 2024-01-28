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
    # Incriments when someone plays, used to determine current player
    turn: Mapped[int] = mapped_column(nullable=False, default=0)

    # Saves the current card to make sure users dont lie about the validity of the card they play
    current_card: Mapped[str] = mapped_column(nullable=True)

    # Whether or not the game is in session
    active: Mapped[bool] = mapped_column(nullable=False, default=False)

    # Save the total value of the +2 currently in game
    p2_value: Mapped[int] = mapped_column(nullable=False, default=0)

    # Save the total value of the +4 currently in game
    p4_value: Mapped[int] = mapped_column(nullable=False, default=0)

    # Setting for if +2s can be stacked
    p2_stack: Mapped[bool] = mapped_column(nullable=True)

    # Setting for if foreign cards (skip, reverse) are allowed on a plus 2 while stacking
    p2_allow_foreign: Mapped[bool] = mapped_column(nullable=False, default=False)

    # Setting for if +4 can be stacked
    p4_stack: Mapped[bool] = mapped_column(nullable=True)

    # Setting for if foreign cards (skip, reverse) are allowed on a plus 4 while stacking
    p4_allow_foreign: Mapped[bool] = mapped_column(nullable=False, default=False)

    # Save the orientation of the game
    orientation: Mapped[int] = mapped_column(nullable=False, default=1)

class RoomPlayer(db.Model):
    __tablename__ = "player_table"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Save the user's name (for this game)
    name: Mapped[str] = mapped_column(nullable=False)

    # Save the user's deck
    deck = mapped_column(MutableList.as_mutable(PickleType), nullable=True)

    # Saves the turn according to the client
    turn: Mapped[int] = mapped_column(nullable=False, default=0)

    # Save the total set of instructions in the game for this player
    instruction_set = mapped_column(MutableList.as_mutable(PickleType), nullable=False, default=[])

    # If the user just played a wild card, this is the string of the card
    wild_card : Mapped[str] = mapped_column(nullable=True)

    room_id = mapped_column(ForeignKey("room_table.id"))
    room: Mapped["Room"] = relationship(back_populates="players")

def init_db(app):
    db.init_app(app)

    with app.app_context():
        db.drop_all()
        db.create_all()
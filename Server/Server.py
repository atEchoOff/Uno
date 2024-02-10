from flask import Flask, render_template, request, session, abort, redirect, url_for
import secrets, json
from flask_session import Session
import os
# FIXME this doesnt work lol
os.system("rm -f ./Client/flask_session/*")

app = Flask(__name__, template_folder="../Client", static_folder="../Client")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///uno.db"
app.secret_key = secrets.token_urlsafe(16)
app.config["SESSION_TYPE"] = "filesystem" # The fact that this isnt default boggles my mind

sess = Session()
sess.init_app(app)

from Database import *
init_db(app)

import Utils, Uno

@app.route('/', methods=["GET", "POST"])
def home():
    # Home page where you can choose to join or create a room
    room_name_error = ""
    user_name_error = ""
    if request.form and "user-name" in request.form and "room-name" in request.form and "action" in request.form:
        # User is sending a post!
        user_name, room_name, action = request.form['user-name'], request.form['room-name'], request.form['action']
        
        # Check for validity
        room_name_error = Utils.valid_room_name(room_name)
        user_name_error = Utils.valid_user_name(user_name)

        if room_name_error == "" and user_name_error == "":
            # There are no errors! We can perform the requested action
            if action == "Create":
                # User wants to create room. First, make sure the room doesnt exist
                if not Utils.room_exists(room_name):
                    # Room doesnt exist, create it!
                    p2_stack = True if "p2stack" in request.form and request.form["p2stack"] == "on" else False
                    p2_allow_foreign = True if "p2foreign" in request.form and request.form["p2foreign"] == "on" else False
                    p4_stack = True if "p4stack" in request.form and request.form["p4stack"] == "on" else False
                    p4_allow_foreign = True if "p4foreign" in request.form and request.form["p4foreign"] == "on" else False
                    wild = True if "wild" in request.form and request.form["wild"] == "on" else False
                    room = Utils.create_room(room_name, p2_stack, p2_allow_foreign, p4_stack, p4_allow_foreign, wild)

                    # Now, add the user
                    Utils.room_player(session, room, _404=False, name=user_name)

                    # Finally, redirect the user to the game page
                    return redirect(url_for("game_room", room_name=room_name))
                else:
                    # Uh oh, room exists. Set error. Then this will jump to render
                    room_name_error = "A room with this name already exists."
            elif action == "Join":
                # User wants to join a room. First, make sure the room exists
                if Utils.room_exists(room_name):
                    # Room exists! Make sure it isnt active
                    room = Utils.room(room_name)
                    if not room.active:
                        # Room is not active and exists, user is free to join!

                        Utils.room_player(session, room, _404=False, name=user_name)

                        # Finally, redirect the user to the game page
                        return redirect(url_for("game_room", room_name=room_name))
                    else:
                        # Uh oh, room is active. Set error. Then this will jump to render
                        room_name_error = "This room is currently in game."
                else:
                    # Uh oh, room doesnt exist. Set error. Then this will jump to render.
                    room_name_error = "A room with this name does not exist."

    return render_template("joinOrCreateRoom.html", room_name_error=room_name_error, user_name_error=user_name_error)

@app.route('/game_room/<room_name>')
def game_room(room_name):
    # The main page for a game of uno
    room = Utils.room(room_name) # 404 if room doesnt exist

    # If the room is active, do not let more people in
    if room.active:
        abort(404)

    player = Utils.room_player(session, room) # This will 404 if the user doesnt belong in this room

    # Let everyone know a player has joined
    # FIXME make it so users cant join twice
    Utils.broadcast(room, [f"USER:{player.name}/{player.id}"], commit=False, exclude=player)

    # Tell the new user all the players currently in the room
    Utils.broadcast(player, [f"USER:{_player.name}/{_player.id}" for _player in room.players])

    return render_template("gameRoom.html", room_name=room_name, 
                                            id=player.id, 
                                            p2_allow_foreign=int(room.p2_allow_foreign), 
                                            p4_allow_foreign=int(room.p4_allow_foreign), 
                                            p2_stack=int(room.p2_stack), 
                                            p4_stack=int(room.p4_stack),
                                            wild=int(room.wild))

@app.route('/start_game/<room_name>')
def start_game(room_name):
    # Start the game! (Called by user in game_room)
    room = Utils.room(room_name) # 404 if doesnt exist
    Utils.room_player(session, room) # This will 404 if the user doesnt belong in this room

    if not room.active:
        room.active = True

        # Give everyone a deck
        for player in room.players:
            deck = [Uno.random_card(room) for _ in range(7)]
            player.deck = deck
            Utils.broadcast(player, ["CARDS:" + json.dumps(deck)], commit=False)

        # Tell everyone the game has started, the current card, and who is up
        room.current_card = Uno.random_card(room, numerical_only=True)
        Utils.broadcast(room, ["START", f"CARD:{room.current_card}", f"TURN:{room.players[room.turn].id}"])
        return ""
    else:
        # The room is already active
        abort(404)

@app.route('/broadcast_hub/<room_name>')
def broadcast_hub(room_name):
    # pythonanywhere does not support SocketIO
    # Instead, users will poll this page
    # Each user for each game has a variable "turn" (client turn)
    # Each user element has an instruction set of instructions
    # If turn(client) < len(instr_set), client has something to learn
    # Dump everything from the instruction set after the (client) turn to the user
    # Then, update the users turn

    room = Utils.room(room_name)
    room_player = Utils.room_player(session, room)

    # Query client turn
    client_turn = room_player.turn
    instruction_set = room_player.instruction_set
    if client_turn < len(instruction_set):
        # User is not up to date, reset their turn and send them the info
        room_player.turn = len(instruction_set)
        tosend = instruction_set[client_turn:]
        db.session.commit()
        return json.dumps(tosend)
    else:
        # User is up to date
        return json.dumps([])

@app.route('/user_broadcast/<room_name>', methods=["GET"])
def user_broadcast(room_name):
    # The user is trying to take a turn
    room = Utils.room(room_name)
    room_player = Utils.room_player(session, room)
    
    # First, make sure the user can do that (its their turn)
    if room_player.id == room.players[room.turn].id:
        # Its the player's turn
        move = request.args.get("msg")

        if room_player.wild_card:
            # User just played a wild card. This move should be a color. Add a simulated card for this color
            # To the deck, and proceed. 
            if move not in "yrgb":
                # Move color is not valid
                abort(404)
            
            # Replace the wild card with a colored version of it
            move = move + room_player.wild_card[1]
            room_player.deck[room_player.deck.index(room_player.wild_card)] = move

        if move == "draw":
            # User requests to draw cards
            # Make sure they can (if they just did, that move is illegal)
            if room_player.instruction_set[-1].startswith("DRAW"):
                # You cant draw!
                abort(404)

            cards = Uno.draw_cards(room)

            # Add the cards to the user's deck
            room_player.deck.extend(cards)

            # Give the cards to the player
            Utils.broadcast(room_player, [f"DRAW:{json.dumps(cards)}"], commit=False)

            # Tell everyone else the user drew however many cards
            Utils.broadcast(room, [f"DREW:{len(cards)}"], exclude=room_player, commit=False)
        elif move == "pass":
            # FIXME this one is controversial
            # Only let the user pass if they have drawn in this turn
            if not room_player.instruction_set[-1].startswith("DRAW"):
                # You cant pass!
                abort(404)

            # Dont let the player pass during a +2 or +4 event
            if room.p2_value > 0 or room.p4_value > 0:
                # Cheater! You cant pass when theres a +2 or +4
                abort(404)

            Uno.next_turn(room)
            Utils.broadcast(room, [f"TURN:{room.players[room.turn].id}"], commit=False)

        elif room_player.wild_card or Uno.card_can_be_played(room, room_player, move):
            # Card played is legal, or a wild card is being moved in
            # Play the card and tell everyone about it
            Uno.play_card(room, room_player, move)
            Utils.broadcast(room, [f"CARD:{move}"], commit=False)

            # Move to the next turn and tell everyone
            Uno.next_turn(room)
            Utils.broadcast(room, [f"TURN:{room.players[room.turn].id}"], commit=False)

            # The user is no longer playing a wild card!
            room_player.wild_card = None
        else:
            # Move wasnt legal and wasnt a draw
            abort(404)

        db.session.commit()
        return ""
    else:
        abort(404)


if __name__ == '__main__':
    app.run(host='localhost', port=9999, debug=True)
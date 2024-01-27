from Database import *
from flask import abort

def valid_room_name(room_name):
    # Return error code for room name validity
    if 0 < len(room_name) <= 20 and room_name.isalnum():
        return ""
    else:
        return "Room name should be between 1 and 20 characters and should be alphanumeric."

def valid_user_name(user_name):
    # Return error code for username validity
    if 0 < len(user_name) <= 20 and user_name.isalnum():
        return ""
    else:
        return "User name should be between 1 and 20 characters and should be alphanumeric."

def room_exists(room_name):
    # Check if a room exists with a certain name
    return Room.query.filter_by(name=room_name)\
                     .count() != 0

def create_room(room_name):
    # Create a room with given name and return it
    room = Room()
    room.name = room_name
    db.session.add(room)
    return room

def room(room_name):
    # Returns the room given the room name
    # 404 if there is none
    return Room.query.filter_by(name=room_name).one_or_404()

def room_player(session, room, _404=True, name=None):
    # Returns the player for the specific room
    # If there is none, create one (set session variables and attach to room)
    # If _404, then 404 instead
    # If user does not exist, given them specified name
    # If in that case name is None, bad!!!

    if 'game_id' not in session:
        # session not initialized, set it up
        if _404:
            abort(404)
        
        session['game_id'] = dict()
        
    if room.name not in session['game_id']:
        # User not tied to game, add new user to db and add user to room
        if _404 or name == None:
            abort(404)
        
        room_player = RoomPlayer(name=name)
        db.session.add(room_player)
        room.players.append(room_player)
        
        db.session.commit()
        session['game_id'][room.name] = room_player.id
        return room_player
    
    return RoomPlayer.query.filter_by(id=session['game_id'][room.name]).one_or_404()

def broadcast(room_or_player, msgs, commit=True, exclude=None):
    # Broadcast a message to the room or to the player
    # If room_or_player is a room, broadcast to all players in room
    # Otherwise, just broadcast to the player
    if isinstance(room_or_player, Room):
        for player in room_or_player.players:
            if player == exclude:
                continue
            player.instruction_set.extend(msgs)
        if commit:
            db.session.commit()
        return
    
    # Otherwise, assume the object is a player
    room_or_player.instruction_set.extend(msgs)
    if commit:
        db.session.commit()
import random
from flask import abort
from Database import db

suits = "wrbgy"

numerical_cards = [suit + val for suit in "rgby" for val in "0112233445566778899"]
special_cards = [suit + val for suit in "rgby" for val in "++ssrr"]
wild_cards = ["w" + val for val in "wwwwpppp"] # ww is wild, wp is wild plus four

def random_card(numerical_only=False):
    # Return a random uno card
    if numerical_only:
        return random.choice(numerical_cards)
    
    card_num = random.randint(0, 107)
    if card_num < len(numerical_cards):
        return numerical_cards[card_num]
    
    card_num -= len(numerical_cards)
    if card_num < len(special_cards):
        return special_cards[card_num]
    
    card_num -= len(special_cards)
    return wild_cards[card_num]

def card_can_be_played(room, room_player, card):
    # Check if new_card can be played on this game
    room_suit, room_val = room.current_card
    card_suit, card_val = card

    if card not in room_player.deck:
        # Player tried playing a card they dont have!
        # A cheater has been spotted...
        # Or just a really bad bug
        return False
    
    if room.p2_value == 0 and room.p4_value == 0:
        # Standard gameflow
        if card_suit == "w":
            return True
        
        return room_suit == card_suit or room_val == card_val
    
    if room.p2_value > 0:
        # A +2 is in action
        if room.p2_allow_foreign:
            return card_val in {"r", "+", "s"}
        else:
            return card_val == "+"
        
    if room.p4_value > 0:
        # A +4 is in action
        if room.p4_allow_foreign:
            return card_val in {"r", "p", "s"}
        else:
            return card_val == "p"
        
    return False

def draw_cards(room):
    # Return a list of drawn cards 
    draw_amt = 1
    if room.p2_value > 0:
        draw_amt = room.p2_value
        room.p2_value = 0
    if room.p4_value > 0:
        draw_amt = room.p4_value
        room.p4_value = 0

    # Get random cards and send off to the user
    return [random_card() for _ in range(draw_amt)]

def next_turn(room):
    # Move a room to the next turn
    # Incriment the turn timer
    room.turn += room.orientation

    # Make sure the turn doesnt leave 0...len(room.players)-1
    if room.turn < 0:
        room.turn += len(room.players)
    if room.turn >= len(room.players):
        room.turn -= len(room.players)

def play_card(room, room_player, move):
    card_value = move[1]
    
    if move[0] == "w":
        # Wild card. The user's next request should be a color
        # Abort for now, but let the user update with a color on their next request
        room_player.wild_card = move
        db.session.commit()
        abort(418)

    if room.p2_value > 0:
        # A +2 is down, figure out the new value based on what they played
        if room.p2_stack and card_value == "+":
            room.p2_value += 2
        elif room.p2_allow_foreign and card_value == "s":
            room.p2_value = 0
        
    elif room.p4_value > 0:
        # A +4 is down, figure out the new value based on what they played
        if room.p4_stack and card_value == "p":
            room.p4_value += 4
        elif room.p4_allow_foreign and card_value == "s":
            room.p4_value = 0

    else:
        # There is no value, the game is normal
        # First, check for special cards
        if card_value == "+":
            # A +2 was played!
            room.p2_value = 2
        elif card_value == "p":
            # A +4 was played!
            room.p4_value = 4
        elif card_value == "s":
            # A skip was played!
            room.turn += room.orientation
        elif card_value == "r":
            # A reverse was played!
            if len(room.players) == 2:
                # This is a 2-player game, so instead just skip
                room.turn += room.orientation
            else:
                room.orientation *= -1

    # Now, just set the current card, remove from players deck, and move on
    room.current_card = move
    room_player.deck.remove(move)
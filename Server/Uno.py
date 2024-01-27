import random

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
    
    card_num -= len(wild_cards)
    return wild_cards[card_num]

def card_can_be_played(game, card):
    # Check if new_card can be played on this game
    game_suit, game_val = game.current_card
    card_suit, card_val = card

    if game_suit == card_suit or game_val == card_val:
        return True
    
    if game.p2_stack and game.p2_allow_foreign:
        # A +2 is being stacked, reverse, +2, or skip is allowed
        if card_val in {"r", "+", "s"}:
            return True
        
    if game.p4_stack and game.p4_allow_foreign:
        # A +4 is being stacked, reverse, +4, or skip is allowed
        if card_val in {"r", "p", "s"}:
            return True
        
    return False
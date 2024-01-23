import random

suits = "wrbgy"

def int_to_uno_card(_int):
    # Convert an integer (0-107) into an uno card
    if 0 <= _int <= 75:
        # It is a numbered card
        suit = suits[_int // 19 + 1]
        if _int % 19 == 0:
            val = 0
        else:
            val = (_int + 1) // 2

        return suit + str(val)
    
    _int -= 76
    if 0 <= _int <= 23:
        # It is an action card
        pass


def random_card(special=True):
    # Return a random uno card
    suits = ""
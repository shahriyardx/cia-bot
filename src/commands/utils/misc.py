import random
from string import ascii_uppercase, digits


def generate_random_string(length: int):
    all_chars = ascii_uppercase + digits
    chars = list(all_chars)
    random.shuffle(chars)

    return "".join(random.choice("".join(chars)) for _ in range(length))

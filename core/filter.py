from core.magic import MAX_WORD_COUNT, MIN_WORD_COUNT, MAX_WORD_LENGTH


def get_max_word_length(s: str) -> int:
    value = 0

    for word in s.split(" "):
        word_length = len(word)
        if word_length > value:
            value = word_length

    return value


def is_valid(message: str) -> bool:
    word_count = len(message.split(" "))
    max_word_length = get_max_word_length(message)
    return MIN_WORD_COUNT <= word_count <= MAX_WORD_COUNT and max_word_length <= MAX_WORD_LENGTH

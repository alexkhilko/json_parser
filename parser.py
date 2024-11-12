import argparse
from enum import auto, Enum


class Status(Enum):
    NOT_STARTED = auto()
    COLLECTING_KEY = auto()
    COLLECTING_VALUE = auto()
    END_KEY = auto()
    END_VALUE = auto()
    WAIT_KEY = auto()
    WAIT_VALUE = auto()
    FINISHED = auto()


to_skip = [" ", "\n"]


def handle_not_started(char: str, tokens, cur_token) -> tuple[Status, str]:
    if char in {"[", "{"}:
        return Status.WAIT_KEY, cur_token
    if char in to_skip:
        return Status.NOT_STARTED, cur_token
    raise Exception(
        f"Invalid json: Invalid character {char} before start. status - not started"
    )


def handle_collecting_key(char: str, tokens, cur_token) -> tuple[Status, str]:
    if char == '"':
        tokens.append(cur_token)
        return Status.END_KEY, ""
    return Status.COLLECTING_KEY, cur_token + char


def handle_collecting_value(char: str, tokens, cur_token) -> tuple[Status, str]:
    if char == '"':
        tokens.append(cur_token)
        return Status.END_VALUE, ""
    return Status.COLLECTING_VALUE, cur_token + char


def handle_end_key(char: str, tokens, cur_token) -> tuple[Status, str]:
    if char in to_skip:
        return Status.END_KEY, cur_token
    if char == ":":
        return Status.WAIT_VALUE, cur_token
    raise Exception(f"Invalid json: expected semicolon. Found {char}. status - end key")


def handle_end_value(char: str, tokens, cur_token) -> tuple[Status, str]:
    if char in to_skip:
        return Status.END_VALUE, cur_token
    if char == ",":
        return Status.WAIT_KEY, cur_token
    if char == "}":
        return Status.FINISHED, cur_token
    raise Exception(f"Invalid json: expected comma. Found {char}. status - end value")


def handle_wait_key(char: str, tokens, cur_token) -> tuple[Status, str]:
    if char == "}" and not tokens:
        return Status.FINISHED, ""
    if char in to_skip:
        return Status.WAIT_KEY, cur_token
    if char == '"':
        return Status.COLLECTING_KEY, ""
    if char == "}" and tokens:
        raise Exception(f"Invalid json: waiting for new key. Found {char}")
    raise Exception(f"Invalid json: expecting quotes. Found {char}. status - wait key")


def handle_wait_value(char: str, tokens, cur_token) -> tuple[Status, str]:
    if char in to_skip:
        return Status.WAIT_VALUE, cur_token
    if char == '"':
        return Status.COLLECTING_VALUE, ""
    raise Exception(
        f"Invalid json: expecting quotes. Found {char}. status - wait value"
    )


def handle_finished(char: str, tokens, cur_token) -> tuple[Status, str]:
    if char in to_skip:
        return Status.FINISHED, cur_token
    raise Exception(
        f"Invalid json: expecting no characters after close bracket. Found {char}. status - finished"
    )


status_handler_map = {
    Status.NOT_STARTED: handle_not_started,
    Status.COLLECTING_KEY: handle_collecting_key,
    Status.COLLECTING_VALUE: handle_collecting_value,
    Status.END_KEY: handle_end_key,
    Status.END_VALUE: handle_end_value,
    Status.WAIT_KEY: handle_wait_key,
    Status.WAIT_VALUE: handle_wait_value,
    Status.FINISHED: handle_finished,
}

def load(file_path: str) -> list[str]:
    tokens = []
    with open(file_path) as f:
        char = f.read(1)
        status = Status.NOT_STARTED
        cur_token = ""
        while char:
            handler = status_handler_map[status]
            status, cur_token = handler(char, tokens, cur_token)
            char = f.read(1)
    if status is Status.NOT_STARTED:
        raise Exception("Invalid json - Empty file.")
    print("Parsed valid JSON file.")
    return tokens


# def load(file_path: str) -> list[str]:
#     tokens = []
#     with open(file_path, 'rb') as f:
#         char = f.read(1)
#         while char:
#             char = f.read(1)
#             print(char)
#     print("Parsed valid JSON file.")
#     return tokens

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("filename")
    args = parser.parse_args()
    load(args.filename)

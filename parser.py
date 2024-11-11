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


def load(file_path: str) -> list[str]:
    tokens = []
    with open(file_path) as f:
        char = f.read(1)
        to_skip = [" ", "\n"]
        status = Status.NOT_STARTED
        cur_token = ""
        while char:
            if status is Status.NOT_STARTED:
                if char in {"[", "{"}:
                    status = Status.WAIT_KEY
                elif char not in to_skip:
                    raise Exception(f"Invalid json: Invalid character {char} before start")
            elif status == Status.FINISHED:
                if char not in to_skip:
                    raise Exception(f"Invalid json: expecting no characters after close bracket. Found {char}")
            else:
                if char == "}":
                    if status == Status.WAIT_KEY and tokens:
                        raise Exception(f"Invalid json: waiting for new key. Found {char}")
                    status = Status.FINISHED
                elif status in {Status.WAIT_KEY, Status.END_KEY, Status.WAIT_VALUE, Status.END_VALUE} and char in to_skip:
                    pass
                elif status is Status.END_KEY and char != ":":
                    raise Exception(f"Invalid json: excected semicolon. Found {char}")
                elif status is Status.END_VALUE and char != ",":
                    raise Exception(f"Invalid json: expected comma. Found {char}")
                elif status in [Status.WAIT_KEY, Status.WAIT_VALUE] and char != '"':
                    raise Exception(f"Invalid json: expecting quotes. Found {char}")
                elif status is Status.WAIT_KEY and char == '"':
                    status = Status.COLLECTING_KEY
                elif status is Status.WAIT_VALUE and char == '"':
                    status = Status.COLLECTING_VALUE
                elif status is Status.COLLECTING_KEY and char == '"':
                    tokens.append(cur_token)
                    cur_token = ""
                    status = Status.END_KEY
                elif status is Status.COLLECTING_VALUE and char == '"':
                    tokens.append(cur_token)
                    cur_token = ""
                    status = Status.END_VALUE
                elif status in [Status.COLLECTING_KEY, Status.COLLECTING_VALUE]:
                    cur_token += char
                elif status is Status.END_KEY and char == ":":
                    status = Status.WAIT_VALUE
                elif status is Status.END_VALUE and char == ",":
                    status = Status.WAIT_KEY
            char = f.read(1)
    if status is Status.NOT_STARTED:
        raise Exception("Invalid json - Empty file.")
    print("Parsed valid JSON file.")
    return tokens


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('filename')  
    args = parser.parse_args()
    load(args.filename)

import argparse
from enum import auto, Enum


# typical lifetime: NOT_STARTED -> WAIT_KEY -> COLLECTING_KEY -> END_KEY -> WAIT_VALUE -> COLLECTING_VALUE -> END_VALUE -> FINISHED
class Status(Enum):
    NOT_STARTED = auto()
    COLLECTING_KEY = auto()
    COLLECTING_VALUE = auto()
    END_KEY = auto()
    END_VALUE = auto()
    WAIT_KEY = auto()
    WAIT_VALUE = auto()
    FINISHED = auto()

to_skip = (" ", "\n")

class JsonLoader:
    def __init__(self, status = Status.NOT_STARTED):
        self.tokens = []
        self.result = {}
        self.status = status
        self.result = {}
        self.cur_token = ""

    def handle_not_started(self, char: str) -> None:
        if char in to_skip:
            return
        if char in {"[", "{"}:
            self.status = Status.WAIT_KEY
            return
        raise Exception(
            f"Invalid json: Invalid character {char} before start. status - not started"
        )

    def handle_collecting_key(self, char: str) -> None:
        if char == '"':
            self.tokens.append(self.cur_token)
            self.status = Status.END_KEY
            self.cur_token = ""
        else:
            self.cur_token += char

    def handle_collecting_value(self, char: str) -> None:
        if char == '"':
            self.tokens.append(self.cur_token)
            self.status = Status.END_VALUE
            self.cur_token = ""
        else:
            self.cur_token += char

    def handle_end_key(self, char: str) -> None:
        if char in to_skip:
            return
        if char == ":":
            self.status = Status.WAIT_VALUE
        else:
            raise Exception(
                f"Invalid json: expected semicolon. Found {char}. status - end key"
            )

    def handle_end_value(self, char: str) -> None:
        if char in to_skip:
            return
        if char == ",":
            self.status = Status.WAIT_KEY
        elif char == "}":
            self.status = Status.FINISHED
        else:
            raise Exception(
                f"Invalid json: expected comma. Found {char}. status - end value"
            )

    def handle_wait_key(self, char: str) -> None:
        if char == "}" and not self.tokens:
            self.status = Status.FINISHED
            self.cur_token = ""
        elif char in to_skip:
            return
        elif char == '"':
            self.status = Status.COLLECTING_KEY
            self.cur_token = ""
        elif char == "}" and self.tokens:
            raise Exception(f"Invalid json: waiting for new key. Found {char}")
        else:
            raise Exception(
                f"Invalid json: expecting quotes. Found {char}. status - wait key"
            )

    def handle_wait_value(self, char: str) -> None:
        if char in to_skip:
            self.status = Status.WAIT_VALUE
        elif char == '"':
            self.status = Status.COLLECTING_VALUE
            self.cur_token = ""
        else:
            raise Exception(
                f"Invalid json: expecting quotes. Found {char}. status - wait value"
            )

    def get_handler(self):
        handler_map = {
            Status.NOT_STARTED: self.handle_not_started,
            Status.COLLECTING_KEY: self.handle_collecting_key,
            Status.COLLECTING_VALUE: self.handle_collecting_value,
            Status.END_KEY: self.handle_end_key,
            Status.END_VALUE: self.handle_end_value,
            Status.WAIT_KEY: self.handle_wait_key,
            Status.WAIT_VALUE: self.handle_wait_value,
        }
        return handler_map[self.status]

    def load_result(self):
        if self.status is Status.END_VALUE and self.tokens:
            self.result[self.tokens[-2]] = self.tokens[-1]

    def load(self, f):
        char = f.read(1)
        while char and self.status is not Status.FINISHED:
            if self.status is Status.WAIT_VALUE and char == "{":
                result = JsonLoader(status=Status.WAIT_KEY).load(f)
                self.tokens.append(result)
                self.status = Status.END_VALUE
            else:
                handler = self.get_handler()
                handler(char)
            self.load_result()
            char = f.read(1)
        if self.status is Status.NOT_STARTED:
            raise Exception("Invalid json - Empty file.")
        return self.result


def load(file_path: str) -> list[str]:
    reader = JsonLoader()
    result = None
    with open(file_path) as f:
        result = reader.load(f)
        char = f.read(1)
        while char:
            if char not in to_skip:
                raise Exception(
                    f"Invalid json: expecting no characters after close bracket. Found {char}. status - finished"
                )
            char = f.read(1)
    return result

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

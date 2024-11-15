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

    @classmethod
    def collecting_statuses(cls):
        return {
            Status.COLLECTING_KEY,
            Status.COLLECTING_VALUE,
        }

chars_to_skip = (" ", "\n")

class JsonLoader:
    def __init__(self, status = Status.NOT_STARTED, result = None):
        self.tokens = []
        self.status = status
        self.result = result
        self.cur_token = ""
        self.is_numeric_token = False
    
    def raise_exception(self, reason):
        raise Exception(
            f"Invalid json: {reason}. status - {self.status}"
        )

    def handle_not_started(self, char: str) -> None:
        if char == "{":
            self.status = Status.WAIT_KEY
            self.result = {}
        elif char == "[":
            self.status = Status.WAIT_VALUE
            self.result = []
        else:
            self.raise_exception(f"Invalid character {char} before start")

    def handle_wait_key(self, char: str) -> None:
        if char == "}" and not self.result:
            self.status = Status.FINISHED
            self.cur_token = ""
        elif char == '"':
            self.status = Status.COLLECTING_KEY
            self.cur_token = ""
        elif char == "}" and self.result:
            self.raise_exception(f"waiting for new key. Found {char}")
        else:
            self.raise_exception(f"expecting quotes. Found {char}")
        
    def handle_collecting_key(self, char: str) -> None:
        if char == '"':
            self.tokens.append(self.cur_token)
            self.status = Status.END_KEY
            self.cur_token = ""
        else:
            self.cur_token += char

    def handle_end_key(self, char: str) -> None:
        if char != ":":
            self.raise_exception(f"expected semicolon. Found {char}")
        self.status = Status.WAIT_VALUE
        
    def handle_wait_value(self, char: str) -> None:
        if char.isdigit() or char in {"-", "+"}:
            self.cur_token = char
            self.status = Status.COLLECTING_VALUE
            self.is_numeric_token = True
        elif char == '"':
            self.status = Status.COLLECTING_VALUE
        else:
            self.raise_exception(f"expecting quotes. Found {char}")
        
    def handle_collecting_value(self, char: str) -> None:
        if char == '"' or (char in chars_to_skip and self.is_numeric_token):
            token = int(self.cur_token) if self.is_numeric_token else self.cur_token
            self.tokens.append(token)
            self.status = Status.END_VALUE
            self.cur_token = ""
        elif char == "," and self.is_numeric_token:
            token = int(self.cur_token) if self.is_numeric_token else self.cur_token
            self.tokens.append(token)
            self.status = Status.WAIT_KEY if self.is_object() else Status.WAIT_VALUE
            self.cur_token = ""
        else:
            if self.is_numeric_token and not char.isdigit():
                self.raise_exception(f"expecting digit token symbol. found: {char}")
            self.cur_token += char
    
    def is_object(self):
        return isinstance(self.result, dict)

    def handle_end_value(self, char: str) -> None:
        if char == ",":
            status = Status.WAIT_KEY if self.is_object() else Status.WAIT_VALUE
            self.status = status
        elif (char == "}" and self.is_object()) or (char == "]" and not self.is_object()):
            self.status = Status.FINISHED
        else:
            self.raise_exception(f"expected comma. Found {char}")

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
        if len(self.tokens) == 0:
            return
        if len(self.tokens) == 2 and self.is_object():
            self.result[self.tokens[-2]] = self.tokens[-1]
            self.tokens = []
        elif not self.is_object():
            self.result.append(self.tokens[-1])
            self.tokens = []


    def load(self, f):
        char = f.read(1)
        while char:
            if char in chars_to_skip and self.status not in Status.collecting_statuses():
                char = f.read(1)
                continue
            if self.status is Status.WAIT_VALUE and char == "{":
                result = JsonLoader(Status.WAIT_KEY, {}).load(f)
                self.tokens.append(result)
                self.status = Status.END_VALUE
            elif self.status is Status.WAIT_VALUE and char == "[":
                result = JsonLoader(Status.WAIT_VALUE, []).load(f)
                self.tokens.append(result)
                self.status = Status.END_VALUE
            else:
                handler = self.get_handler()
                handler(char)
            self.load_result()
            if self.status is Status.FINISHED:
                break
            char = f.read(1)
        if self.status is Status.NOT_STARTED:
            self.raise_exception("Empty file")
        return self.result


def load(file_path: str) -> list[str]:
    reader = JsonLoader()
    result = None
    with open(file_path) as f:
        result = reader.load(f)
        char = f.read(1)
        while char:
            if char not in chars_to_skip:
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

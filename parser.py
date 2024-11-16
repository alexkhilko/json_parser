import argparse
from enum import auto, Enum

from json_parser.exceptions import InvalidTokenException


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
    

class TokenType(Enum):
    STRING = auto()
    NUMBER = auto()
    # true, false, null
    MIX = auto()

EMPTY_CHARS = (" ", "\n")

class Token:
    def __init__(self, token_type: TokenType = TokenType.STRING, value: str = ""):
        self.type = token_type
        self._value = value
    
    MIX_TOKENS = {
        "null": None,
        "true": True,
        "false": False,
    }
    
    def validate_next_char(self, char: str):
        if self.type is TokenType.NUMBER and not char.isdigit():
            raise InvalidTokenException(char)
        if self.type is TokenType.MIX:
            token = self._value + char
            if not any(token == option[:len(token)] for option in self.MIX_TOKENS):
                raise InvalidTokenException(token)
    
    def _validate_final_token(self):
        if self.type is not TokenType.MIX:
            return
        if self._value not in self.MIX_TOKENS:
            raise InvalidTokenException(self._value)
    
    def get_value(self):
        self._validate_final_token()
        if self.type is TokenType.NUMBER:
            return int(self._value)
        if self.type is TokenType.MIX:
            return self.MIX_TOKENS[self._value]
        return self._value
    
    def add(self, char: str):
        self._value += char
    
    def update(self, value: str, token_type: TokenType):
        self._value = value
        self.type = token_type

    def reset(self):
        self._value = ""
        self.type = TokenType.STRING


class JsonLoader:
    def __init__(self, status=Status.NOT_STARTED, result=None):
        self.tokens = []
        self.status = status
        self.result = result
        self.cur_token = Token()
    
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
            self.cur_token.reset()
        elif char == '"':
            self.status = Status.COLLECTING_KEY
            self.cur_token.reset()
        elif char == "}" and self.result:
            self.raise_exception(f"waiting for new key. Found {char}")
        else:
            self.raise_exception(f"expecting quotes. Found {char}")
        
    def handle_collecting_key(self, char: str) -> None:
        if char == '"':
            self.tokens.append(self.cur_token.get_value())
            self.status = Status.END_KEY
            self.cur_token.reset()
        else:
            self.cur_token.add(char)

    def handle_end_key(self, char: str) -> None:
        if char != ":":
            self.raise_exception(f"expected semicolon. Found {char}")
        self.status = Status.WAIT_VALUE
        
    def handle_wait_value(self, char: str) -> None:
        if char.isdigit() or char == "-":
            self.cur_token.update(value=char, token_type=TokenType.NUMBER)
        elif char == '"':
            self.cur_token.update(value="", token_type=TokenType.STRING)
        else:
            self.cur_token.update(value=char, token_type=TokenType.MIX)
        self.status = Status.COLLECTING_VALUE
    
    def handle_collecting_value(self, char: str) -> None:
        if (char == '"' and self.cur_token.type is TokenType.STRING) or ((char in EMPTY_CHARS or char == ",") and self.cur_token.type is not TokenType.STRING):
            self.tokens.append(self.cur_token.get_value())
            self.cur_token.reset()
            if char == ",":
                self.status = Status.WAIT_KEY if self.is_object() else Status.WAIT_VALUE
            else:
                self.status = Status.END_VALUE
        else:
            self.cur_token.validate_next_char(char)
            self.cur_token.add(char)
    
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
            if char in EMPTY_CHARS and self.status not in Status.collecting_statuses():
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


def load(file_path: str, encoding: str = "utf-8") -> list[str]:
    reader = JsonLoader()
    result = None
    with open(file_path, encoding=encoding) as f:
        result = reader.load(f)
        char = f.read(1)
        while char:
            if char not in EMPTY_CHARS:
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
    result = load(args.filename)
    print(result)


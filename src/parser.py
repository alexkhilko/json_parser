from enum import auto, Enum

from .token import Token, TokenType
from .exceptions import InvalidJsonException

# typical lifetime:  WAIT_KEY -> COLLECTING_KEY -> END_KEY -> WAIT_VALUE -> COLLECTING_VALUE -> END_VALUE -> FINISHED
class Status(Enum):
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

EMPTY_CHARS = (" ", "\n")


class JsonStateMachine:
    def __init__(self, status, result):
        self.status = status
        self.result = result
        self.tokens = []
        self.cur_token = Token()
    
    @classmethod
    def from_char(cls, char):
        if char == "{":
            return cls(Status.WAIT_KEY, {})
        if char == "[":
            return cls(Status.WAIT_VALUE, [])
        raise InvalidJsonException(
            f"Invalid character {char} before start."
        )
    
    def _raise_exception(self, reason):
        raise InvalidJsonException(
            f"{reason}. status - {self.status}"
        )

    def _is_end_of_token(self, char: str) -> bool:
        if self.cur_token.type is TokenType.STRING:
            return char == '"'
        return char in EMPTY_CHARS or char == "," or char == "}" or char == "]"
    
    def _is_object(self):
        return isinstance(self.result, dict)
    
    def _is_finish_symbol(self, char: str) -> bool:
        finish_char = "}" if self._is_object() else "]"
        return finish_char == char
    
    def _handle_wait_key(self, char: str) -> None:
        if char == "}" and not self.result:
            self.status = Status.FINISHED
            self.cur_token.reset()
        elif char == '"':
            self.status = Status.COLLECTING_KEY
            self.cur_token.reset()
        elif char == "}" and self.result:
            self._raise_exception(f"waiting for new key. Found {char}")
        else:
            self._raise_exception(f"expecting quotes. Found {char}")
        
    def _handle_collecting_key(self, char: str) -> None:
        if char == '"':
            self.tokens.append(self.cur_token.get_value())
            self.status = Status.END_KEY
            self.cur_token.reset()
        else:
            self.cur_token.add(char)

    def _handle_end_key(self, char: str) -> None:
        if char != ":":
            self._raise_exception(f"expected semicolon. Found {char}")
        self.status = Status.WAIT_VALUE
        
    def _handle_wait_value(self, char: str) -> None:
        if char.isdigit() or char == "-":
            self.cur_token.update(value=char, token_type=TokenType.NUMBER)
        elif char == '"':
            self.cur_token.update(value="", token_type=TokenType.STRING)
        else:
            self.cur_token.update(value=char, token_type=TokenType.MIX)
        self.status = Status.COLLECTING_VALUE
    
    def _handle_collecting_value(self, char: str) -> None:
        if self._is_end_of_token(char):
            self.tokens.append(self.cur_token.get_value())
            self.cur_token.reset()
            if char == ",":
                self.status = Status.WAIT_KEY if self._is_object() else Status.WAIT_VALUE
            elif self._is_finish_symbol(char):
                self.status = Status.FINISHED
            else:
                self.status = Status.END_VALUE
        else:
            self.cur_token.validate_next_char(char)
            self.cur_token.add(char)
    
    def _handle_end_value(self, char: str) -> None:
        if char == ",":
            status = Status.WAIT_KEY if self._is_object() else Status.WAIT_VALUE
            self.status = status
        elif self._is_finish_symbol(char):
            self.status = Status.FINISHED
        else:
            self._raise_exception(f"expected comma. Found {char}")

    def get_state_handler(self):
        handler_map = {
            Status.WAIT_KEY: self._handle_wait_key,
            Status.WAIT_VALUE: self._handle_wait_value,
            Status.COLLECTING_KEY: self._handle_collecting_key,
            Status.COLLECTING_VALUE: self._handle_collecting_value,
            Status.END_KEY: self._handle_end_key,
            Status.END_VALUE: self._handle_end_value,
        }
        return handler_map[self.status]

    def load_result(self):
        if len(self.tokens) == 0:
            return
        if len(self.tokens) == 2 and self._is_object():
            self.result[self.tokens[-2]] = self.tokens[-1]
            self.tokens = []
        elif not self._is_object():
            self.result.append(self.tokens[-1])
            self.tokens = []


def _load(file_, char):
    state_machine = JsonStateMachine.from_char(char)
    while char and state_machine.status is not Status.FINISHED:
        char = file_.read(1)
        if char in EMPTY_CHARS and state_machine.status not in Status.collecting_statuses():
            continue
        if char in {"{", "["}:
            state_machine.tokens.append(_load(file_, char))
            state_machine.status = Status.END_VALUE
        else:
            state_handler = state_machine.get_state_handler()
            state_handler(char)
        state_machine.load_result()
    return state_machine.result


def load(file_path: str, encoding: str = "utf-8") -> list[str]:
    with open(file_path, encoding=encoding) as f:
        char = f.read(1)
        while char in EMPTY_CHARS:
            char = f.read(1)
        if char is None:
            raise InvalidJsonException("Empty file")
        result = _load(f, char)
        char = f.read(1)
        while char:
            if char not in EMPTY_CHARS:
                raise InvalidJsonException(
                    f"expecting no characters after closing bracket. Found {char}."
                )
            char = f.read(1)
        return result

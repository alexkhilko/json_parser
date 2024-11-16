from enum import auto, Enum

from .exceptions import InvalidTokenException

class TokenType(Enum):
    STRING = auto()
    NUMBER = auto()
    # true, false, null
    MIX = auto()


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

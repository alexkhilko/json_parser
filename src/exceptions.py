class InvalidTokenException(Exception):
    def __init__(self, token):
        self.invalid_token = token
        self.message = f"Invalid token value. Expecting string, number, null, true, false. Found: {token}."
        super().__init__(self.message)


class InvalidJsonException(Exception):
    def __init__(self, reason):
        self.reason = reason
        self.message = f"Invalid json: {reason}."
        super().__init__(self.message)

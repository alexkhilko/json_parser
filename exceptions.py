class InvalidTokenException(Exception):
    def __init__(self, token):
        self.invalid_token = token
        self.message = f"Invalid token value. Expecting string, number, null, true, false. Found: {token}."
        super().__init__(self.message)
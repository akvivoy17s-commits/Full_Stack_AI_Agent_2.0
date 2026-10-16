class ApiError(Exception):
    """One error type for the whole API. The client always sees {"error": {"code", "message", "details"?}}."""

    def __init__(self, status: int, code: str, message: str, details: dict | None = None):
        super().__init__(message)
        self.status, self.code, self.message, self.details = status, code, message, details

    def body(self) -> dict:
        err = {"code": self.code, "message": self.message}
        if self.details:
            err["details"] = self.details
        return {"error": err}


def validation_failed(message: str = "Invalid input", details: dict | None = None) -> ApiError:
    return ApiError(400, "validation_failed", message, details)

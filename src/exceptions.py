# global exceptions
from fastapi import status
from enum import Enum


class BaseErrorMessage(Enum):
    def __init__(self, http_status: status, error_code: int, message: str):
        self.http_status: status = http_status
        self.error_code = error_code
        self.message = message


class DefaultErrorMessage(BaseErrorMessage):
    """
    error_code: 9000번대
    """

    SERVER_ERROR = status.HTTP_500_INTERNAL_SERVER_ERROR, 9000, "server error"
    NOT_FOUND = status.HTTP_404_NOT_FOUND, 9001, "not found"
    UNAUTHORIZED = status.HTTP_401_UNAUTHORIZED, 9002, "unauthorized"
    DB_ERROR_VALIDATION = status.HTTP_422_UNPROCESSABLE_ENTITY, 9006, "validation error"

class APIExcpetion(Exception):
    def __init__(self, error_message: BaseErrorMessage, added_message=None):
        self.error_message = error_message
        self.added_message = added_message

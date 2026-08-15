'''
docstring for ErrorHandler.py
Error handler comes with two things:
primary use: to take errors, log them, wrap them, raise them.
'''
from .logger import loggy
from enum import Enum

def log(log: str) -> None:
    loggy("utils/ErrorHandler", log)

class ErrorHandler(Exception):
    '''
    Docstring for ErrorHandler
    when you inherit Exception class you can raise the instances of ErrorHandler
    '''

    def __init__(self, status_code:int, message: str, errCode: int, error: Exception):
        self.status_code = status_code
        self.message = message
        self.errCode = errCode
        self.error = error


def initiate_error_handler(message: str, errCode: int, error: Exception):
    '''
    Docstring for initiate_error_handler 
    This creates a ErrorHandler instance, logs the errors, and raises the instance to heavens (endpoint).
    '''
    log(f"Error occurred: {message}, with error code: {errCode}, exception type: {type(error).__name__}, and exception message: {str(error)}")


    # we can internally decide the status code with http_deferred_error
    status_code = http_deferred_error[errCode]
    Seraphina = ErrorHandler(status_code=status_code, message=message, errCode=errCode, error=error)
    raise Seraphina
    # and the endpoint will catch it and send the response.


# ------------------ ENUMS ------------------- #

class ErrorCodes(Enum):
    # --------------- 1000s for Dock layer --------------- #
    INVALID_PAYLOAD_CONTENT = 1001
    UNRECOGNIZED_UNIQUE_ID = 1002

    # -------------- 2000S for Operations Layer -----------#
    CANNOT_CREATE_OPERATION_STATE = 2001
    OPERATION_ID_ALREADY_EXISTS = 2002
    UNRECOGNIZED_OPERATION_ID = 2003
    OPERATION_VERIFICATION_FAILED = 2004

    # --------------- 3000s for ORM layer ---------------- #
    DATABASE_CONNECTION_FAILED = 3001
    CANNOT_ADD_ENTRY_TO_DATABASE = 3002
    UNEXPECTED_DUPLICATE_ENTRY = 3003
    FIELD_ALREADY_EXISTS = 3004
    BROAD_DATABASE_ERROR = 3005
    USER_NOT_FOUND = 3006
    KEY_NOT_FOUND = 3007

    # ------------------ 4000s for user module -------------- #
    INVALID_EMAIL_FORMAT = 4001
    INVALID_USERNAME_FORMAT = 4002
    INVALID_PASSWORD_FORMAT = 4003
    INCORRECT_PASSWORD = 4004
    CANNOT_CREATE_SESSION = 4005

    # ------------------ 9000s for validators ---------------- #
    INCORRECT_TEMPORAL_TYPE = 9001
    INCORRECT_TEMPORAL_FORMAT = 9002

http_deferred_error: dict[int, int] = {
    ErrorCodes.INVALID_PAYLOAD_CONTENT.value: 400,
    ErrorCodes.OPERATION_ID_ALREADY_EXISTS.value: 409,
    ErrorCodes.UNRECOGNIZED_OPERATION_ID.value: 404,
    ErrorCodes.OPERATION_VERIFICATION_FAILED.value: 400,
    ErrorCodes.CANNOT_CREATE_OPERATION_STATE.value: 500,
    ErrorCodes.UNRECOGNIZED_UNIQUE_ID.value: 404,
    ErrorCodes.DATABASE_CONNECTION_FAILED.value: 500,
    ErrorCodes.INVALID_EMAIL_FORMAT.value: 400,
    ErrorCodes.INCORRECT_TEMPORAL_TYPE.value: 400,
    ErrorCodes.INCORRECT_TEMPORAL_FORMAT.value: 400,
    ErrorCodes.CANNOT_ADD_ENTRY_TO_DATABASE.value: 500,
    ErrorCodes.INVALID_USERNAME_FORMAT.value: 400,
    ErrorCodes.INVALID_PASSWORD_FORMAT.value: 400,
    ErrorCodes.FIELD_ALREADY_EXISTS.value: 409,
    ErrorCodes.USER_NOT_FOUND.value: 404,
    ErrorCodes.KEY_NOT_FOUND.value: 404,
    ErrorCodes.BROAD_DATABASE_ERROR.value: 500,
    ErrorCodes.INCORRECT_PASSWORD.value: 401,
    ErrorCodes.CANNOT_CREATE_SESSION.value: 500
}
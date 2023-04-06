from fastapi import FastAPI, Request
from src.schemas import DefaultReponse
from fastapi.responses import JSONResponse
from tortoise.exceptions import OperationalError, DBConnectionError, DoesNotExist, IntegrityError
from fastapi.exceptions import RequestValidationError
import traceback
import logging
from src.exceptions import *
from bson.errors import InvalidId


def make_errors(http_status: int, **kwargs) -> JSONResponse:
    logging.error(traceback.format_exc())
    res_obj = DefaultReponse.parse_obj(kwargs)
    return JSONResponse(content=res_obj.dict(), status_code=http_status)


def register_exception_handler(base_api: FastAPI):
    @base_api.exception_handler(APIExcpetion)
    async def default_api_error_handler(request: Request, exc: APIExcpetion):
        logging.debug(traceback.format_exc())
        return make_errors(exc.error_message.http_status, error_code=exc.error_message.error_code, result=exc.error_message.message, added_message=exc.added_message)

    @base_api.exception_handler(Exception)
    async def default_server_error_handler(request: Request, exc: Exception):
        error_message = DefaultErrorMessage.SERVER_ERROR
        logging.error(traceback.format_exc())
        return make_errors(error_message.http_status, error_code=error_message.error_code, result=error_message.message)

    @base_api.exception_handler(OperationalError)
    async def default_tortoise_operationalerror_handler(request: Request, exc: OperationalError):
        error_message = DefaultErrorMessage.DB_OPERATION_ERROR
        logging.error(traceback.format_exc())
        return make_errors(error_message.http_status, error_code=error_message.error_code, result=error_message.message)

    @base_api.exception_handler(DBConnectionError)
    async def default_tortoise_dbconnectionerror_handler(request: Request, exc: DBConnectionError):
        error_message = DefaultErrorMessage.DB_CONNECT_ERROR
        logging.error(traceback.format_exc())
        return make_errors(error_message.http_status, error_code=error_message.error_code, result=error_message.message)

    @base_api.exception_handler(DoesNotExist)
    async def doesnotexist_exception_handler(request: Request, exc: DoesNotExist):
        error_message = DefaultErrorMessage.DB_ERROR_DOESNOTEXIST
        logging.error(traceback.format_exc())
        return make_errors(error_message.http_status, error_code=error_message.error_code, result={"message": error_message.message, "trace": str(exc)})

    @base_api.exception_handler(IntegrityError)
    async def integrityerror_exception_handler(request: Request, exc: IntegrityError):
        error_message = DefaultErrorMessage.DB_ERROR_INTEGRITYERROR
        logging.error(traceback.format_exc())
        return make_errors(error_message.http_status, error_code=error_message.error_code, result={"message": error_message.message, "trace": str(exc)})

    @base_api.exception_handler(RequestValidationError)
    async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
        error_message = DefaultErrorMessage.DB_ERROR_VALIDATION
        logging.error(traceback.format_exc())
        return make_errors(error_message.http_status, error_code=error_message.error_code, result={"message": error_message.message, "trace": str(exc)})

    @base_api.exception_handler(InvalidId)
    async def mongodb_connect_exception_handler(request: Request, exc: InvalidId):
        error_message = DefaultErrorMessage.MONGDB_INVALID_OBJECT_ID
        logging.error(traceback.format_exc())
        return make_errors(error_message.http_status, error_code=error_message.error_code, result={"message": error_message.message, "trace": str(exc)})

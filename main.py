import uvicorn

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.background import BackgroundTask
from starlette.types import Message
from src import config, utils
import os
import config_loader
import logging
import exception_handlers
import traceback
from decimal import getcontext

# Decimal 타입 사용 시 여유를 위해 추가
getcontext().prec = 40
getcontext().Emax = 9999999999
getcontext().Emin = -9999999999

os.environ.setdefault("SERVER_CONFIG", "local")

base_doc_url = ""

base_api = FastAPI(
    version="1.0.0",
    title="kakaotalk analysis",
    description="카카오 대화분석",
    docs_url=f"{base_doc_url}/docs",
    redoc_url=f"{base_doc_url}/redoc",
    openapi_url=f"{base_doc_url}/openapi.json",
)

base_api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ex) http://localhost, http://localhost:8080, https://localhost.tiangolo.com, http://localhost.tiangolo.com, ...
    allow_credentials=False,  # allow_origins가 있는 경우에만 True (*는 사용 못함)
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception 핸들러 등록용
exception_handlers.register_exception_handler(base_api)


# request, response body 로깅용
def log_info(req_body=None, res_body=None):
    logging.debug(f"request body: {req_body}")
    # logging.debug(f"response body: {res_body}")
    return


async def set_body(request: Request, body: bytes):
    async def receive() -> Message:
        return {"type": "http.request", "body": body}

    request._receive = receive


@base_api.middleware("http")
async def request_logging(request: Request, call_next):
    url = request.url.path
    req_body = await request.body()
    await set_body(request, req_body)
    try:
        response = await call_next(request)
    except Exception:
        logging.warn(traceback.format_exc())
        response = None

    res_body = b""
    if response:
        async for chunk in response.body_iterator:
            res_body += chunk

    task = None
    if req_body:
        task = BackgroundTask(log_info, f"{request.method} {url} {req_body}", f"{request.method} {url} {res_body}")
    return Response(content=res_body, status_code=response.status_code, headers=dict(response.headers), media_type=response.media_type, background=task)


if __name__ == "__main__":
    config_loader.init()
    log_config_path = "./appconfig/logging.ini"
    if not os.path.exists(log_config_path):
        server = os.environ.get("SERVER_CONFIG")
        log_config_path = f"./appconfig/logging_{server}.ini"
    uvicorn.run(
        "main:base_api",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=config.API_RELOAD,
        workers=config.API_WORKERS,
        log_config=log_config_path,
    )


# fast api가 정상적으로 올라오면 할 작업
@base_api.on_event("startup")
async def api_start_up_event():
    # api import
    import src.auto_api_list

    logging.info("server start up")


# fast api가 종료될 때 할 작업 (ctrl+c 등의 종료 이벤트를 받게 되는 경우)
@base_api.on_event("shutdown")
async def api_start_up_event():
    await utils.graceful_shutdown()
    logging.info("server shutdown")

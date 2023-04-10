# 각 모듈의 url 라우터 (controller)

from main import base_api
from fastapi import APIRouter, UploadFile, File, Response, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from . import service_ios
from . import service_android
from src.schemas import DefaultReponse
from datetime import date
import io
import os
import re
from datetime import datetime as dt
from zipfile import ZipFile, BadZipFile
import traceback
import logging

route = APIRouter(prefix="/kakao", tags=["kakao analysis"])
MAX_COUNT = 10

BASE_DIR = os.path.abspath("")

templates = Jinja2Templates(directory="static")
templates.env.globals["STATIC_URL"] = "/static"

base_api.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")


@route.post("/analysis", response_model=DefaultReponse)
async def kakao_analysis(start: str, end: str, kakao_talk_zip: UploadFile = File(default=None)):
    current_timestamp = str(dt.now().timestamp()).replace(".", "")
    logging.info(f"{current_timestamp}: start analysis")
    start = dt.strptime(re.sub("\D", "", start), "%Y%m%d").date()
    end = dt.strptime(re.sub("\D", "", end), "%Y%m%d").date()
    result = await analysis(start, end, kakao_talk_zip, current_timestamp)

    return DefaultReponse.success(result)


async def analysis(start: date, end: date, kakao_talk_zip: UploadFile, current_timestamp: str):
    file_data = await kakao_talk_zip.read()
    logging.info(f"{current_timestamp} file read finished")
    zip_io = io.BytesIO(file_data)
    try:
        ZipFile(zip_io)
        return await service_ios.analysis(start, end, zip_io, current_timestamp)
    except BadZipFile:
        return await service_android.analysis(start, end, file_data, current_timestamp)


@route.get("/index")
async def kakao_analysis(request: Request):
    return templates.TemplateResponse("html/index.html", context={"request": request})


@route.get("/css")
async def kakao_analysis(request: Request):
    return templates.TemplateResponse("html/base.css", context={"request": request})


# @route.post("/analysis")
# async def kakao_analysis(start: date, end: date, kakao_talk_zip: UploadFile = File(default=None)):
#     # print(font_manager.findSystemFonts())
#     result = await service.analysis(start, end, kakao_talk_zip)
#     all_sum = sum(result.values())
#     all_count = len(result)
#     max_page = int(all_count / MAX_COUNT) + 1 if all_count % MAX_COUNT > 0 else 0

#     pie_labels = []
#     pie_values = []
#     pie_explode = []

#     stack_lables = []
#     stack_values = []

#     count = 0
#     for name, value in result.items():
#         count += 1
#         if count <= 10:
#             pie_labels.append(f"{name} / {value}")
#             pie_values.append(round(value / all_sum * 100, 1))
#             pie_explode.append(0.3)

#         stack_lables.append(name)
#         stack_values.append(value)

#     rc("font", family="AppleGothic")
#     # plt.rcParams["figure.figsize"] = [7.50, 4.50]
#     plt.rcParams["figure.autolayout"] = True
#     plt.rcParams["axes.unicode_minus"] = False

#     plot_size = max_page + 1
#     plot_idx = 1

#     plt.subplot(plot_size, 1, plot_idx)
#     plt.pie(pie_values, labels=pie_labels, autopct="%.1f%%", startangle=90, counterclock=False, explode=pie_explode)
#     plt.title("10위권 점유율")

#     try:
#         for i in range(max_page):
#             plot_idx += 1
#             plt.subplot(plot_size, 1, plot_idx)
#             start_idx = i * MAX_COUNT
#             end_idx = start_idx + MAX_COUNT

#             s_values = stack_values[start_idx:end_idx]
#             s_lables = stack_lables[start_idx:end_idx]
#             stack_y = np.arange(len(s_values))

#             if i + 1 < max_page:
#                 s_values = stack_values[start_idx:end_idx]
#                 s_lables = stack_lables[start_idx:end_idx]

#             else:
#                 s_values = stack_values[start_idx:]
#                 s_lables = stack_lables[start_idx:]

#             plt.barh(stack_y, s_values, height=0.6)
#             plt.yticks(stack_y, s_lables)
#             plt.title(f"전체 순위: {i+1}")
#     except Exception:
#         logging.warn(traceback.format_exc())

#     # plt.legend(loc="lower right")

#     img_buf = io.BytesIO()
#     plt.savefig(img_buf, format="png", dpi=200, bbox_inches="tight", pad_inches=0.5)
#     plt.close()

#     headers = {"Content-Disposition": 'inline; filename="out.png"'}
#     return Response(img_buf.getvalue(), headers=headers, media_type="image/png")


base_api.include_router(route)

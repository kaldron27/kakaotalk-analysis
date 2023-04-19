import logging
from src.exceptions import *
from datetime import datetime as dt
import os
import shutil
import traceback
import io
import re
from datetime import date
from . import service
from konlpy.tag import Okt
from .stop_words import *


okt = Okt()

# 대화 예시
# 2023. 2. 20. 09:53, 닉네임 : 대화
# 시작은 날짜 시간
# 쉼표 구분으로 닉네임
# 첫 : 이후 메시지

regex = re.compile("^\d{4}년\s\d{1,2}월\s\d{1,2}일\s(오전|오후)\s\d{1,2}:\d{2},")  # 대화 메시지
etc_regex = re.compile("^\d{4}년\s\d{1,2}월\s\d{1,2}일\s(오전|오후)\s\d{1,2}:\d{2},")  # 나간사람, 들어온사람, 내보내진사람은 콜론 (:)이 없음

text_compile = re.compile("[^ ㄱ-ㅣ가-힣]+")  # 한글 분석

inner = "님이 들어왔습니다."
outer = "님이 나갔습니다."
kick = "님을 내보냈습니다."
hidden = "채팅방 관리자가 메시지를 가렸습니다."

# 2023. 3. 23. 21:03, 초롱초롱 튜브 : 왜 벌써
# 2023. 3. 26. 22:21: 일하기 싫은 네오님이 들어왔습니다.
# 2023. 3. 27. 22:34: 츄리닝안경 네오님을 내보냈습니다.
# 2023. 3. 23. 16:06: 초롱초롱 튜브님이 나갔습니다.
# 2023. 3. 23. 21:04: 채팅방 관리자가 메시지를 가렸습니다.


async def analysis(start: date, end: date, kakao_talk_zip: bytes, current_timestamp: str, kick_count: int, kick_per_day: int):
    logging.info(f"{current_timestamp} start android analysis")
    temp_dir = os.path.abspath("temp/" + current_timestamp)
    analysis_text = []
    message = {}
    etc_msg = {"inner": {}, "outer": {}, "kick": {}, "hidden": 0}
    try:
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        all_messages = kakao_talk_zip.decode().splitlines()

        logging_idx = int(len(all_messages) / 10) + 1
        logging.info(f"{current_timestamp} file line length: {len(all_messages)}")

        idx = 0

        for l_str in all_messages:
            if idx % logging_idx == 0:
                logging.info(f"{current_timestamp}: reading string size: {len(l_str)}")
            idx += 1
            col_idx = l_str.rfind(":")
            com_idx = l_str.find(",")
            if regex.match(l_str) and col_idx > com_idx:
                try:
                    if "," in l_str:
                        try:
                            date_idx, t_date = await _get_date_(l_str)
                        except Exception:
                            continue
                        if t_date >= start:
                            if t_date > end:
                                return await service._sort_message_(message, etc_msg, start, end, kick_count, kick_per_day, analysis_text)
                            # t_time = full_time.time()
                            other_str = l_str[date_idx:].strip()
                            nick_idx = other_str.index(":")
                            nick = other_str[1:nick_idx].strip()
                            # text = other_str[nick_idx + 1 :].strip()
                            # add_text = okt.pos(text_compile.sub("", text))
                            # for txt, txt_type in add_text:
                            #     if txt_type in ("Noun", "Verb"):
                            #         if txt not in stop_words:
                            #             analysis_text.append(txt)

                            if nick not in message:
                                message[nick] = 0
                            message[nick] += 1
                except Exception:
                    logging.warn(traceback.format_exc())

            if etc_regex.match(l_str) and col_idx < com_idx:
                try:
                    if "," in l_str:
                        str_list = l_str.split(",")
                        date_str = str_list[0].strip()
                        date_str = await _transfer_date_(date_str)
                        current_date = dt.strptime(date_str, "%Y. %m. %d. %H:%M")
                        t_date = current_date.date()
                        msg: str = str_list[1].strip()

                        nick = ""
                        if inner in msg:
                            nick = msg.replace(inner, "")
                            etc_msg["inner"][nick] = current_date
                        elif outer in msg:
                            nick = msg.replace(outer, "")
                            etc_msg["outer"][nick] = current_date
                        elif kick in msg:
                            nick = msg.replace(kick, "")
                            etc_msg["kick"][nick] = current_date
                        elif hidden in msg:
                            etc_msg["hidden"] += 1

                        if nick not in message and nick:
                            message[nick] = 0

                except Exception:
                    logging.warn(traceback.format_exc())
                    continue

    except Exception:
        logging.error(traceback.format_exc())
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

    return await service._sort_message_(message, etc_msg, start, end, kick_count, kick_per_day, analysis_text)


async def _get_first_msg_(messages: list):
    idx = 0
    for msg in messages:
        if regex.match(msg):
            return msg
        idx += 1
    return None


async def _get_last_msg_(messages: list):
    length = len(messages)
    max_idx = length - 1
    for i in range(length):
        idx = max_idx - i
        msg = messages[idx]
        if regex.match(msg):
            return msg
    return None


async def _get_date_(line_text: str):
    date_idx = line_text.index(",")
    date = await _transfer_date_(line_text[:date_idx])
    full_time: dt = dt.strptime(date, "%Y. %m. %d. %H:%M")
    return date_idx, full_time.date()


async def _transfer_date_(date_str: str):
    date_str = date_str.replace("년", ".").replace("월", ".").replace("일", ".")
    add_hours = 0
    if "오후" in date_str:
        date_str = date_str.replace("오후 ", "")
        add_hours = 12
    else:
        date_str = date_str.replace("오전 ", "")

    date_split = date_str.split(".")
    time_split = date_split[-1].split(":")
    date_split = date_split[:-1]
    hours = time_split[0].strip()
    minutes = time_split[1].strip().zfill(2)
    if hours == "12":
        if add_hours == 12:
            add_hours = 0
        elif add_hours == 0:
            add_hours = -12
    hours = str(int(hours) + add_hours).zfill(2)

    date_str = ".".join(date_split) + ". " + hours + ":" + minutes
    return date_str

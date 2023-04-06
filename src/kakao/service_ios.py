import logging
from src.exceptions import *
from datetime import datetime as dt
from zipfile import ZipFile
import os
import shutil
import traceback
import io
import re
from datetime import date
from io import BytesIO
from . import service
from konlpy.tag import Okt
from .stop_words import *

okt = Okt()

# 대화 예시
# 2023. 2. 20. 09:53, 닉네임 : 대화
# 시작은 날짜 시간
# 쉼표 구분으로 닉네임
# 첫 : 이후 메시지

regex = re.compile("^\d{4}\.\s\d{1,2}\.\s\d{1,2}\.\s\d{2}:\d{2},")  # 대화 메시지
etc_regex = re.compile("^\d{4}\.\s\d{1,2}\.\s\d{1,2}\.\s\d{2}:\d{2}:")  # 나간사람, 들어온사람, 내보내진사람

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


async def analysis(start: date, end: date, kakao_talk_zip: BytesIO):
    temp_dir = os.path.abspath("temp/" + str(dt.now().timestamp()).replace(".", ""))
    analysis_text = []
    message = {}
    etc_msg = {"inner": {}, "outer": {}, "kick": {}, "hidden": 0}
    try:
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        with ZipFile(kakao_talk_zip) as f:
            f.extractall(temp_dir)

        talk_list = os.listdir(temp_dir)
        for file_name in talk_list:
            try:
                f_names = file_name.split("-")
                name = f_names[1].split(".")[0].zfill(30)
                shutil.move(f"{temp_dir}/{file_name}", f"{temp_dir}/{name}")
                os.chmod(f"{temp_dir}/{name}", 0o777)
            except Exception:
                logging.warn(traceback.format_exc())

        talk_list = os.listdir(temp_dir)
        talk_list.sort()
        for file_name in talk_list:
            with open(f"{temp_dir}/{file_name}", "r") as f:
                all_messages = f.readlines()[4:]
                first_msg = await _get_first_msg_(all_messages)
                last_msg = await _get_last_msg_(all_messages)
                first_idx, first_date = await _get_date_(first_msg)
                last_idx, last_date = await _get_date_(last_msg)

                if first_date > end:
                    break
                if not ((first_date <= start and start <= last_date) or (first_date <= end and end <= last_date) or (start <= first_date and first_date <= end) or (start <= last_date and last_date <= end)):
                    continue

                for l_str in all_messages:
                    if regex.match(l_str):
                        try:
                            if "," in l_str:
                                try:
                                    date_idx, t_date = await _get_date_(l_str)
                                except Exception:
                                    continue
                                if t_date < start:
                                    continue
                                if t_date > end:
                                    return await service._sort_message_(message, etc_msg, start, end, analysis_text)
                                # t_time = full_time.time()
                                other_str = l_str[date_idx:].strip()
                                nick_idx = other_str.index(":")
                                nick = other_str[1:nick_idx].strip()
                                text = other_str[nick_idx + 1 :].strip().lower()
                                add_text = okt.pos(text_compile.sub("", text))
                                for txt, txt_type in add_text:
                                    if txt_type in ("Noun", "Verb"):
                                        if txt not in stop_words:
                                            analysis_text.append(txt)

                                if nick not in message:
                                    message[nick] = 0
                                message[nick] += 1
                        except Exception:
                            logging.warn(traceback.format_exc())
                            continue
                    if etc_regex.match(l_str):
                        try:
                            if ":" in l_str:
                                str_list = l_str.split(":")
                                date_str = ":".join([str_list[0].strip(), str_list[1].strip()])
                                current_date = dt.strptime(date_str, "%Y. %m. %d. %H:%M")
                                t_date = current_date.date()
                                msg: str = str_list[2].strip()

                                if t_date < start or t_date > end:
                                    continue

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

                        except Exception:
                            logging.warn(traceback.format_exc())
                            continue

    except Exception:
        logging.error(traceback.format_exc())
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

    return await service._sort_message_(message, etc_msg, start, end, analysis_text)


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
    full_time: dt = dt.strptime(line_text[:date_idx], "%Y. %m. %d. %H:%M")
    return date_idx, full_time.date()

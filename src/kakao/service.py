from fastapi import UploadFile
import logging
from src.exceptions import *
from datetime import date, datetime as dt
import datetime
import pandas as pd


OLDER_TIMEDELTA = datetime.timedelta(days=60)
TIME_FORMAT = "%Y-%m-%d %H:%M"


async def _sort_message_(message: dict, etc_msg: dict, start: date, end: date, kick, kick_per_day: int, analysis_text: list = []):
    logging.info("sort messages")
    count_list = []
    allcount = 0
    ranking = 1
    today = dt.now().date()
    older_day = today - OLDER_TIMEDELTA
    for name, count in dict(sorted(message.items(), key=lambda item: item[1], reverse=True)).items():
        date_type = {"date": None, "type": None, "code": None}
        inner_date = None
        if name in etc_msg["inner"]:
            current_date = etc_msg["inner"][name]
            inner_date = current_date.strftime(TIME_FORMAT)
            if date_type["date"] is not None:
                if current_date >= date_type["date"]:
                    date_type["date"] = current_date
                    date_type["type"] = "신입🫶🏼"
                    date_type["code"] = "newb"

            else:
                date_type["date"] = current_date
                date_type["type"] = "신입🫶🏼"
                date_type["code"] = "newb"

        if name in etc_msg["outer"]:
            current_date = etc_msg["outer"][name]
            if date_type["date"] is not None:
                if current_date >= date_type["date"]:
                    date_type["date"] = current_date
                    date_type["type"] = "나감ㅠ"
                    date_type["code"] = "out"
            else:
                date_type["date"] = current_date
                date_type["type"] = "나감ㅠ"
                date_type["code"] = "out"

        if name in etc_msg["kick"]:
            current_date = etc_msg["kick"][name]
            if date_type["date"] is not None:
                if current_date >= date_type["date"]:
                    date_type["date"] = current_date
                    date_type["type"] = "강퇴🧨"
                    date_type["code"] = "kick"
            else:
                date_type["date"] = current_date
                date_type["type"] = "강퇴🧨"
                date_type["code"] = "kick"

        if date_type["date"] is None or (date_type["code"] == "newb" and date_type["date"].date() < start):
            date_type["code"] = "older"
            date_type["type"] = None
            if date_type["date"] is None:
                date_type["type"] = "언제오셨지❗️❓"
                date_type["date"] = "????-??-?? ??:??:??"
            else:
                if date_type["date"].date() < older_day:
                    date_type["type"] = "고인물🫡"
                else:
                    date_type["type"] = "고여가는중💧"

        if date_type["code"] in ("older", "newb") or (date_type["date"].date() >= start and date_type["date"].date() <= end):
            allcount += count
            if date_type["code"] in ("out", "kick") and inner_date is None:
                inner_date = "????-??-?? ??:??:??"
            add_count_data = {"name": f"{name}", "count": count, "condition": date_type["type"], "condition_date": date_type["date"], "condition_code": date_type["code"], "ranking": ranking, "inner_date": inner_date}
            count_list.append(add_count_data)
            ranking += 1

    if allcount == 0:
        raise APIExcpetion(DefaultErrorMessage.NOT_FOUND_TEXT_RANGE)
    # viewer = [f"집계일자: {start}~{end}", f"총 대화량: {allcount}"]
    for data in count_list:
        text_count = data["count"]
        rate = round(text_count / allcount * 100, 2)
        data["rate"] = rate

        condition_code = data["condition_code"]
        is_kick = False

        if condition_code == "older":
            is_kick = text_count <= kick
        elif condition_code == "newb":
            newb_days = (end - data["condition_date"].date()).days + 1
            newb_kick_count = kick_per_day * newb_days
            is_kick = text_count <= kick and text_count <= newb_kick_count

        data["is_kick"] = is_kick
        if type(data["condition_date"]) == dt:
            data["condition_date"] = data["condition_date"].strftime(TIME_FORMAT)
        data["condition_str"] = ""
        if data["condition"] is not None:
            if data["inner_date"] is not None and data["condition_code"] in ("out", "kick"):
                data["condition_str"] = f" ({data['condition']}, {data['inner_date']} ~ {data['condition_date']})"
            else:
                data["condition_str"] = f" ({data['condition']}, {data['condition_date']})"

        # viewer_str = f"{data['ranking']}위: {data['name']} ({data['count']}회 / {rate}%)"
        # if data["condition"] is not None:
        #     viewer_str += f' ({data["condition"]}, {data["condition_date"]})'
        # viewer.append(viewer_str)

    result = {"date_range": f"{start} ~ {end}"}
    result["all_rankers"] = count_list
    result["allcount"] = f"집계일자: {start}~{end}, 총 대화량: {allcount}"
    # result["top_rankers"] = count_list[:10]
    # result["viewer"] = viewer

    # text_result = await _analysis_text_(analysis_text)
    # result["words"] = text_result
    return result


# async def _analysis_text_(text: list):
#     all_word_df = pd.DataFrame({"words": text, "count": len(text) * [1]})
#     all_word_df = all_word_df.groupby("words").count()
#     result_dict = all_word_df.sort_values("count", ascending=False).head(50).to_dict()
#     result = []
#     for words, count in result_dict.get("count").items():
#         result.append({"words": words, "count": count})
#     return result

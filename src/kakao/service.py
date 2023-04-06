from fastapi import UploadFile
import logging
from src.exceptions import *
from datetime import date
import pandas as pd


async def _sort_message_(message: dict, etc_msg: dict, start: date, end: date, analysis_text: list = []):
    count_list = []
    allcount = 0
    ranking = 0
    for name, count in dict(sorted(message.items(), key=lambda item: item[1], reverse=True)).items():
        ranking += 1
        date_type = {"date": None, "type": None, "code": None}
        if name in etc_msg["inner"]:
            current_date = etc_msg["inner"][name]
            if date_type["date"] is not None:
                if current_date > date_type["date"]:
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
                if current_date > date_type["date"]:
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
                if current_date > date_type["date"]:
                    date_type["date"] = current_date
                    date_type["type"] = "강퇴🧨"
                    date_type["code"] = "kick"
            else:
                date_type["date"] = current_date
                date_type["type"] = "강퇴🧨"
                date_type["code"] = "kick"

        if date_type["code"] is None:
            date_type["code"] = "older"

        allcount += count
        count_list.append({"name": f"{name}", "count": count, "condition": date_type["type"], "condition_date": date_type["date"], "condition_code": date_type["code"], "ranking": ranking})

    # viewer = [f"집계일자: {start}~{end}", f"총 대화량: {allcount}"]
    for data in count_list:
        rate = round(data["count"] / allcount * 100, 2)
        data["rate"] = rate
        # viewer_str = f"{data['ranking']}위: {data['name']} ({data['count']}회 / {rate}%)"
        # if data["condition"] is not None:
        #     viewer_str += f' ({data["condition"]}, {data["condition_date"]})'
        # viewer.append(viewer_str)

    result = {"date_range": f"{start} ~ {end}"}
    result["all_rankers"] = count_list
    result["allcount"] = f"집계일자: {start}~{end}, 총 대화량: {allcount}"
    # result["top_rankers"] = count_list[:10]
    # result["viewer"] = viewer

    text_result = await _analysis_text_(analysis_text)
    result["words"] = text_result
    return result


async def _analysis_text_(text: list):
    all_word_df = pd.DataFrame({"words": text, "count": len(text) * [1]})
    all_word_df = all_word_df.groupby("words").count()
    result_dict = all_word_df.sort_values("count", ascending=False).head(25).to_dict()
    result = []
    for words, count in result_dict.get("count").items():
        result.append({"words": words, "count": count})
    return result

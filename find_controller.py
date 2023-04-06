import os
import re
import traceback
import configparser
from pathlib import Path

re_integer = re.compile("\d+$")
re_float = re.compile("\d+[.]\d+$")

api_list_file = open("src/auto_api_list.py", "w+")
model_list_file = open("src/auto_model_list.py", "w+")

models = []


def find_controller(dirname, first_dirname):
    try:
        filenames = os.listdir(dirname)
        for filename in filenames:
            full_filename = os.path.join(dirname, filename)
            if os.path.isdir(full_filename):
                find_controller(full_filename, first_dirname)
            else:
                current_filename = full_filename.split("/")[-1]
                if "api.py" in current_filename:
                    import_name = full_filename.replace(first_dirname + "/", "").replace(".py", "").replace("/", ".")
                    api_list_file.write(f"import {import_name}\n")
                    print(import_name)
    except PermissionError:
        pass


# models.py 자동 등록
def find_models(dirname, first_dirname):
    # controller에 해당하는 api.py가 포함된 파일 import
    try:
        filenames = os.listdir(dirname)
        for filename in filenames:
            full_filename = os.path.join(dirname, filename)
            if os.path.isdir(full_filename):
                find_models(full_filename, first_dirname)
            else:
                current_filename = full_filename.split("/")[-1]
                if "models.py" in current_filename:
                    import_name = full_filename.replace(first_dirname + "/", "").replace(".py", "").replace("/", ".")
                    models.append(import_name)
    except PermissionError:
        pass


def make_appconfig():
    try:
        config = configparser.ConfigParser()
        config.read("appconfig/config.ini", encoding="utf-8")
        appconfig_file = open("src/config.py", "w+")
        home_path = os.path.expanduser("~")

        appconfig_file.write("def set_var(key, value):\n")
        appconfig_file.write("    globals()[key] = value\n\n")

        for cf in config.items():
            for section in cf[1].items():
                if cf == "DEFAULT":
                    key = section[0].upper()
                else:
                    key = f"{cf[0]}_{section[0].upper()}"

                if "-" in key:
                    raise RuntimeError("do not available character '-' in config file")
                value = section[1]
                if value == "None":
                    value = None
                elif value in ("Y", "true", "True", "TRUE"):
                    value = True
                elif value in ("N", "false", "False", "FALSE"):
                    value = False
                elif re_integer.match(value) is not None:
                    value = int(value)
                elif re_float.match(value) is not None:
                    value = float(value)
                else:
                    value = value.replace("~", home_path)
                    value = f"'{value}'"
                appconfig_file.write(f"{key} = None\n")

        appconfig_file.flush()
        appconfig_file.close()
    except RuntimeError as re:
        print(traceback.format_exc())
        raise re
    except Exception:
        print(traceback.format_exc())
        raise Exception("check appconfig/config.ini")


dir_name = str(Path(__file__).resolve().parent) + "/src"
first_name = str(Path(__file__).resolve().parent)
find_controller(dir_name, first_name)
find_models(dir_name, first_name)
model_list_file.write(f"models = {models}")

api_list_file.flush()
api_list_file.close()
model_list_file.flush()
model_list_file.close()

make_appconfig()

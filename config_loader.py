import configparser
import logging
import re
import os
from src import config as appconfig
import traceback

re_integer = re.compile("\d+$")
re_float = re.compile("\d+[.]\d+$")


def init():
    try:
        server = os.environ.get("SERVER_CONFIG")
        if server == "local":
            import find_controller

        config = configparser.ConfigParser()
        config_file_path = "./appconfig/config.ini"
        config.read(config_file_path, encoding="utf-8")
        home_path = os.path.expanduser("~")

        for cf in config.items():
            for section in cf[1].items():
                if cf == "DEFAULT":
                    key = section[0].upper()
                else:
                    key = f"{cf[0]}_{section[0].upper()}"

                if "-" in key:
                    raise RuntimeError("do not available character '-' in config file")
                if_value = section[1].lower()
                value = section[1]
                if if_value in ("none", "null"):
                    value = None
                elif if_value in ("y", "true"):
                    value = True
                elif if_value in ("n", "false"):
                    value = False
                elif re_integer.match(if_value) is not None:
                    value = int(value)
                elif re_float.match(if_value) is not None:
                    value = float(value)
                else:
                    value = value.replace("~", home_path)

                appconfig.set_var(key, value)
    except RuntimeError as re:
        logging.error(traceback.format_exc())
        raise re
    except Exception:
        logging.error(traceback.format_exc())
        raise Exception(f"check your server parameter: {server}")

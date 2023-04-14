import json
from os import makedirs
from os.path import exists, join

import pandas as pd
from dotenv import dotenv_values
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

env = dotenv_values()


def response_multidim(variables: list, frame: pd.DataFrame) -> str:
    """
    Function to prepare msg in MD browser.

    :param variables:
    :param frame:
    :return str:
    """
    common = set(variables).intersection(frame.columns)
    msg = f"{len(common)}/{len(variables)} inputted variables present in the current dataset:"
    msg = msg + "\n" + ", ".join(common)

    return msg


def check_if_exists(data_path, sample_type: str, file_type: str) -> bool:
    """
    Function to check if directory exists.

    :param data_path:
    :param sample_type:
    :param file_type:
    :return boolean:
    """
    path = join(data_path, sample_type, file_type)
    return exists(path)


def load_config(path: str = "config.json") -> dict:
    """
    Function to load config file.

    :param path:
    :return dict:
    """
    with open(path, "r", encoding="utf-8") as config_file:
        return json.load(config_file)


def temp_file_path(
    data_type: str, group_A: str, group_B: str, alpha: float, effect: float, base: str = "temp/"
) -> str:
    """
    Function to generate path to temp file.

    :param data_type:
    :param group_A:
    :param group_B:
    :param alpha:
    :param effect:
    :param base:
    :return str:
    """
    makedirs(base, exist_ok=True)

    file_name = f"{data_type}_{group_A}_{group_B}_{alpha}_{effect}.parquet"
    file_name = file_name.replace("/", "-")
    path = join(base, file_name)

    return path


def load_news(path: str = "text.news") -> str:
    """
    Function to load news from news file.

    :param path:
    :return str:
    """
    if not exists(path):
        with open(path, "x", encoding="utf-8") as file:
            pass
        return ""

    with open(path, "r", encoding="utf-8") as file:
        news = file.read()

    return news


def send_slack_msg(
    source: str, msg: str, channel: str = "edave", token=env["SLACK_API_TOKEN"]
) -> None:
    """
    Function send notification via slack app.

    :param source:
    :param msg:
    :param channel:
    :param token:
    :return:
    """
    if token:
        client = WebClient(token=token)
        try:
            client.chat_postMessage(channel=channel, text=f"Message from: {source} --> {msg}")
        except SlackApiError as e:
            print(f"Error sending message: {e}")

    else:
        print("Slack notification turned off.")

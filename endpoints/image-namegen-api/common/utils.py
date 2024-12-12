"""
A place for common utilities
"""
import csv
import logging
import os
import random
import re
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import pandas as pd
import requests

import yaml
from requests import ConnectTimeout, RequestException, Response
from datetime import datetime, timedelta

# ssojwt = get_jwt_token()
# headers = {
#     "Authorization": f"sso-jwt {ssojwt}",
#     "Content-Type": "application/json"
# }

# provider_options =  {
#     "model": "gpt-4o",
#     "provider": "openai_chat",
#     "moderateProvider": "openai",
#     "moderatePrompt": True,
#     "moderateTemplate": True,
#     "max_tokens": 1000,
#     "temperature": 0.7,
#     "top_p": 1,
#     "frequency_penalty": 0,
#     "presence_penalty": 0,
# }

def read_yaml_file_to_dict(file_path: str) -> Optional[Dict]:
    """
    Read a YAML file and return its contents as a Python dictionary.

    Args:
        file_path (str): The path to the YAML file.

    Returns:
        dict or None: A Python dictionary representing the YAML data, or None if there was an error reading the file.
    """
    try:
        with open(file_path, 'r') as yaml_file:
            yaml_data = yaml.safe_load(yaml_file)
        return yaml_data
    except Exception as e:
        print(f"Error reading YAML file: {e}")
        return None


def configure_logging(name: str, log_path: str = "./log.log") -> logging.Logger:
    """
    Configures and returns a logging.Logger instance for the given module name.

    Args:
        name (str): The name of the module to configure logging for.
        log_path (str): Path to the log file

    Returns:
        logging.Logger: Configured logger for this module.

    Example:
        LOG = configure_logging("MODULE NAME")
    """

    # Set the timezone for the entire process to PST
    os.environ['TZ'] = 'America/Los_Angeles'
    time.tzset()

    log_format = '%(asctime)s PST | %(levelname)s | %(name)s | %(message)s'
    date_format = '%Y/%m/%d %H:%M:%S'  # YYYY/MM/DD HH:MM:SS

    logging_level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR
    }
    level = logging_level_map.get(os.getenv("log_level", "INFO").upper(), logging.INFO)

    logging.basicConfig(
        level=level,
        format=log_format,
        datefmt=date_format,
        handlers=[logging.FileHandler(log_path), logging.StreamHandler()]
    )

    return logging.getLogger(name)


def join_path_and_filename(path: str, filename: str) -> str:
    """
    Joins a path and a filename together, ensuring that there is only one '/' character between them.

    Args:
        path (str): The path to join.
        filename (str): The filename to join.

    Returns:
        str: The joined path and filename.

    """
    # Remove any '/' characters from the end of the path
    while path.endswith('/'):
        path = path[:-1]

    # Remove any '/' characters from the start of the filename
    while filename.startswith('/'):
        filename = filename[1:]

    return os.path.join(path, filename)


def send_get_request(url: str, logger: logging.Logger, timeout: int = 10) -> Response:
    """
    Sends a GET request to the specified URL and returns the response.
    Args:
        url (str): The URL to send the GET request to.
        logger (logging.Logger): The logger instance to log messages.
        timeout (int): The timeout for the GET request in milliseconds. Defaults to 10 sec.

    Returns:
        Response: The response object from the GET request.
    """
    try:
        response = requests.get(url, timeout=timeout)
        return response
    except ConnectTimeout as e:
        logger.error(f"Connection timed out during the GET request: {e}")
        return create_error_response(str(e), 408)  # 408 Request Timeout
    except ConnectionError as e:
        logger.error(f"Connection error occurred during the GET request, possibly due to DNS resolution failure: {e}")
        return create_error_response(str(e), 503)  # 503 Service Unavailable
    except RequestException as e:
        logger.error(f"An error occurred during the GET request: {e}")
        return create_error_response(str(e), 500)  # 500 Internal Server Error


def create_error_response(error_message: str, status_code: int) -> Response:
    """
    Creates a custom Response object with an error message and status code.

    Args:
        error_message (str): The error message to include in the response.
        status_code (int): The HTTP status code to set for the response.

    Returns:
        Response: A custom Response object containing the error information.
    """
    response = Response()
    response.status_code = status_code
    response._content = error_message.encode('utf-8')
    return response


def format_number(value: float | int, decimal_count: int = 2) -> str:
    """
    Format a number with a specified number of decimal places and include comma separators.

    Parameters:
    value (float | int): The number to be formatted.
    decimal_count (int): The desired number of decimal places. Defaults to 2.

    Returns:
    str: The formatted number as a string with comma separators and the specified number of decimal places.
    """
    if not isinstance(value, (float, int)):
        return str(value)

    if not isinstance(decimal_count, int) or decimal_count < 0:
        decimal_count = 2

    format_string = f"{{:,.{decimal_count}f}}"
    return format_string.format(value)




def get_environment() -> str:
    """
    Returns the environment based on the environment variable set
    Returns:
        str: The environment
    """
    environment = (
        "test"
        if os.environ.get("aws_env", "dev") in ["test", "ote"]
        else os.environ.get("aws_env", "dev")
    )
    return environment


def get_caas_url(environment, path="v1/prompts") -> str:
    """
    Returns the CAAS URL based on the environment and path provided
    Args:
        environment (str): The environment to use for the URL
        path (str): The path to append to the base URL
    Returns:
        str: The CAAS URL
    """
    base_url = urljoin("https://caas.api.{}.com", path)
    return base_url.format(
        "dev-godaddy"
        if not environment
        else "godaddy"
        if environment == "prod"
        else f"{environment}-godaddy"
    )


# def run_thread(id):
#     url = f"https://caas.api.godaddy.com/v1/threads/{id}/run"
#     resp = requests.post(url, headers=headers, json=provider_options)

# def get_messages(id):
#     url = f"https://caas.api.godaddy.com/v1/threads/{id}"
#     resp = requests.post(url, headers=headers)
#     try:
#         return resp.json()['data']['value']
#     except Exception as e:
#         # print(traceback.format_exc())
#         print(resp.json())
#         return 

# def process_conversation_gocass(msg, role, id, system_prompt):
#     if id:
#         data = {
#         "messages": [
#                 {
#                 "from": role,
#                 "content": msg,
#                 }
#             ]
#             }
#         url = f"https://caas.api.godaddy.com/v1/threads/{id}"
#         resp = requests.patch(url, headers=headers, json=data)
#         # print(resp)
#         print('calling run thread')
#         return id
#     else:
#         url = "https://caas.api.godaddy.com/v1/threads"
#         data = {
#                 "name": "Domainality",
#                 "description": "customer thread",
#                 "messages": [
#                     system_prompt,
#                     {
#                         "from": role,
#                         "content":msg
#                     }
#                 ],
#                 "provider": "openai_chat",
#                 "providerOptions": provider_options
#                 }
#         response = requests.post(url, headers=headers, json=data)
#         # print(response.json())
#         id = response.json()['data']['id']
#         return id

# def delete_thread(id):
#     url = f"https://caas.api.godaddy.com/v1/threads/{id}"
#     resp = requests.delete(url, headers=headers)
#     # print(resp)



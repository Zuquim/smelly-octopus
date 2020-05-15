from csv import writer
from datetime import datetime as dt
from logging import DEBUG, INFO
from os import getcwd, listdir, system
from socket import gethostname
from subprocess import Popen, PIPE
from sys import exit
from typing import List

from logzero import setup_logger

from GitHub.GraphQL import Query

log = setup_logger(name="tools", level=DEBUG)

# Some constants
output_path = f"{getcwd()}/output"


def notify_owner(message: str):
    # Notify code owner via local Telegram Bot script (none provided in project)
    if gethostname() == "heisenberg":
        system(f"st '{message}'")


def sys_cmd(cmd: list) -> str:
    """Execute system commands using subprocess.Popen()."""

    out, err = Popen(cmd, stdout=PIPE, stderr=PIPE).communicate()
    # Checking return code
    if err != b"":
        log.error(err.decode())
        notify_owner(f"Exited(1) for: {err.decode()}")
        exit(1)
    else:
        return out.decode()


def first_run(gql_query: Query) -> tuple:
    gql = gql_query
    try:
        nodes = gql.json["data"]["search"]["nodes"]
    except KeyError as e:
        log.debug(f"Doing issues | Exception: {e}")
        nodes = gql.json["data"]["repository"]["issues"]["nodes"]
    table_headers = nodes[0].keys()
    log.info(f"Total nodes after first run: {len(nodes)}")

    return gql, table_headers, nodes


def get_repositories(gql_query: Query, node_list: list) -> tuple:
    while gql_query.next_page():
        gql_query.request()
        log.debug(f"Total nodes after last run: {len(node_list)}")
        node_list += gql_query.json["data"]["search"]["nodes"]
    log.info(f"Total nodes after final run: {len(node_list)}")

    return gql_query, node_list


def get_issues(gql_query: Query, node_list: list) -> tuple:
    while gql_query.next_page():
        gql_query.request()
        log.debug(f"Total nodes after last run: {len(node_list)}")
        node_list += gql_query.json["data"]["search"]["nodes"]
    log.info(f"Total nodes after final run: {len(node_list)}")

    return gql_query, node_list


def age_in_seconds(created_at: str, format: str = "%Y-%m-%dT%H:%M:%SZ") -> float:
    return (dt.today() - dt.strptime(created_at, format)).total_seconds()


def save_csv(file_name: str, table_headers: list, node_list: List[dict]):
    if not file_name.endswith(".csv"):
        file_name += ".csv"
    with open(f"{output_path}/{file_name}", "w") as f:
        csv = writer(f)
        csv.writerow(table_headers)
        for repository in node_list:
            log.debug(f"repository={repository}")
            csv.writerow(repository.values())


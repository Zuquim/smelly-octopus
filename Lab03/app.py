from logging import DEBUG, INFO
from os import makedirs
from os.path import exists
from sys import exit

import pandas as pd
from logzero import setup_logger

from GitHub.GraphQL import *
from GitHub.tools import *

log = setup_logger(
    name="main",
    level=DEBUG,
    logfile="lab03.log",
    fileLoglevel=DEBUG,
    maxBytes=1024000,
    backupCount=4,
)

# Loading token string
_token_file = "graphql.token"
log.info(f"Loading GitHub GraphQL token from {_token_file}")
if exists(_token_file):
    with open(_token_file, "r") as t:
        token = t.read()
else:
    log.warning(f"Token file ({_token_file}) not found. Asking for user input...")
    token = input("Insert token string: ")

# Stripping blanks from token
token = token.strip()

# Checking token string
_token_length = 40
log.debug(f"_token='{token}'; len(_token)={len(token)};")
if len(token) != _token_length:
    log.error(
        f"Provided token length ({len(token)}) does not match "
        f"expected length ({_token_length})!"
    )
    exit(1)

# Defining request parameters
url = "https://api.github.com/graphql"
headers = {
    "Accept": "application/vnd.github.v4.idl",
    "Authorization": f"bearer {token}",
}

# Sprint 01
log.info("Getting repositories...")
if not exists(f"{output_path}/repositories.csv"):
    # First run
    query_repos = Query(url, headers, templates["repositories"], auto_run=True)
    query_repos, table_headers, nodes = first_run(query_repos)

    # Getting nodes for the next pages
    query_repos, nodes = get_repositories(query_repos, nodes)

    # Fixing nodes' dictionaries
    _, nodes = fix_dictionaries(query_repos, nodes)

    # Saving repositories data to CSV file inside 'output' directory
    save_csv("repositories", table_headers, nodes)
else:
    log.info(f"CSV file for repositories already exist. Skipping...")

log.info("Got repositories!")

log.info("Getting issues...")
# Getting repositories data
df = pd.read_csv(f"{output_path}/repositories.csv")

for id_, owner_name, n_issues in zip(
        df["id"], df["nameWithOwner"], df["all_issues"]
):
    owner = owner_name.split("/")[0]
    name = owner_name.split("/")[1]
    if not exists(f"{output_path}/{owner}_{name}_issues.csv"):
        log.info(f"Getting issues for: {owner_name}")

        # Skipping if issues=0
        if n_issues < 1:
            log.warning(f"Skipping {owner_name}. Zero issues found.")
            continue

        # Setting max nodes per page
        if n_issues > 50:
            max_per_page = 50
        else:
            max_per_page = n_issues

        # First run
        query_issue = Query(
            url,
            headers,
            templates["issues"],
            n_issues=n_issues,
            max_per_page=max_per_page
        )
        query_issue.update_data_template(owner=owner, name=name)
        query_issue.request()
        query_issue, table_headers, nodes = first_run(query_issue)

        # Getting nodes for the next pages
        query_issue, nodes = get_issues(query_issue, nodes, n_issues)

        # Fixing nodes' dictionaries
        _, nodes = fix_dictionaries(query_issue, nodes)

        # Saving issues data to CSV file inside 'output' directory
        save_csv(f"{owner}_{name}_issues", table_headers, nodes, "")
    else:
        log.info(f"CSV file for '{owner_name}' issues already exist. Skipping...")

log.info("Got repositories!")

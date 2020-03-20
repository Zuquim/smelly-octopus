from logging import DEBUG, INFO
from os import listdir, makedirs
from os.path import exists
from sys import exit

import pandas as pd
from logzero import setup_logger

from GitHub.GraphQL import Query
from GitHub.tools import *

l = setup_logger(name="main", level=INFO)

# Loading token string
_token_file = "graphql.token"
l.info(f"Loading GitHub GraphQL token from {_token_file}")
if exists(_token_file):
    with open(_token_file, "r") as t:
        _token = t.read()
else:
    l.warning(f"Token file ({_token_file}) not found. Asking for user input...")
    _token = input("Insert token string: ")

# Stripping blanks from token
_token = _token.strip()

# Checking token string
_token_length = 40
l.debug(f"_token='{_token}'; len(_token)={len(_token)};")
if len(_token) != _token_length:
    l.error(
        f"Provided token length ({len(_token)}) does not match "
        f"expected length ({_token_length})!"
    )
    exit(1)

# Defining request parameters
url = "https://api.github.com/graphql"
headers = {
    "Accept": "application/vnd.github.v4.idl",
    "Authorization": f"bearer {_token}",
}

# Sprint 01
l.info("Running Sprint 01")

# Step 1
first_step = "guido_repos"
if not exists(f"{output_path}/{first_step}.csv"):
    # First run
    query_01 = Query(url, headers, data_template)
    query_01, table_headers, nodes = first_run(query_01)

    # Getting nodes for the next pages
    query_01, nodes = get_me_a_thousand(query_01, nodes)

    # Fixing node dictionaries
    _, nodes = fix_dictionaries(query_01, nodes)

    # Saving repositories data to CSV file inside 'output' directory
    save_csv(first_step, table_headers, nodes)
else:
    l.info(f"CSV file for '{first_step}' already exist. Skipping...")
l.info("Finished Sprint 01, first step (1/4)")

# Step 2
data_template = data_template.replace("user:gvanrossum language", "language")
second_step = "python_repos"
if not exists(f"{output_path}/{second_step}.csv"):
    # First run
    query_02 = Query(url, headers, data_template)
    query_02, table_headers, nodes = first_run(query_02)

    # Getting nodes for the next pages
    query_02, nodes = get_me_a_thousand(query_02, nodes)

    # Fixing node dictionaries
    query_02, nodes = fix_dictionaries(query_02, nodes)

    # Saving repositories data to CSV file inside 'output' directory
    save_csv(second_step, table_headers, nodes)
else:
    l.info(f"CSV file for '{second_step}' already exist. Skipping...")
l.info("Finished Sprint 01, second step (2/4)")

# Step 3
# Making temporary directory to store cloned repositories
repos_path = f"/tmp/repositories"
if not exists(repos_path):
    makedirs(repos_path)

csv_dir = listdir(output_path)
for csv in csv_dir:
    if csv.endswith(".loc"):
        i = 0
        # Continuing from checkpoint
        df = pd.read_csv(f"{output_path}/{csv}")
        try:
            while df.LoC.get(i) != -1 and i <= df.LoC.__len__():
                i += 1
                l.debug(f"i={i}")
        except KeyError as e:
            l.warning(f"Finished rows. | i={i} | e={e}")
            continue
        l.info(f"Continuing stopped job on {csv} line #{i}...")
        # Cloning repositories and getting a list of LoC sum for each one
        df, loc_list = read_repos_table(csv, repos_path, output_path, i)
    elif csv[:4] == "LoC_" or f"{csv}.loc" in csv_dir:
        # Either already finished or still in progress. Skipping original file...
        continue
    else:
        # Cloning repositories and getting a list of LoC sum for each one
        df, loc_list = read_repos_table(csv, repos_path, output_path)


l.info("Finished Sprint 01, third step (3/4)")

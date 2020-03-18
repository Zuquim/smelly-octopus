from logging import DEBUG, INFO
from os import getcwd, listdir, makedirs
from os.path import exists
from subprocess import Popen, PIPE
from sys import exit

import git
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


# First run
query_01 = Query(url, headers, data_template)
query_01, table_headers, nodes = first_run(query_01)

# Getting nodes for the next pages
query_01, nodes = get_me_a_thousand(query_01, nodes)

# Fixing node dictionaries
_, nodes = fix_dictionaries(query_01, nodes)

# Saving repositories data to CSV file inside 'output' directory
save_csv("guido_repos", table_headers, nodes)

l.info("Finished Sprint 01, first step (1/4)")

# Step 2
data_template = data_template.replace("user:gvanrossum language", "language")
# First run
query_02 = Query(url, headers, data_template)
query_02, table_headers, nodes = first_run(query_02)

# Getting nodes for the next pages
query_02, nodes = get_me_a_thousand(query_02, nodes)

# Fixing node dictionaries
query_02, nodes = fix_dictionaries(query_02, nodes)

# Saving repositories data to CSV file inside 'output' directory
save_csv("python_repos", table_headers, nodes)

l.info("Finished Sprint 01, second step (2/4)")

# Step 3
# Making temporary directory to store cloned repositories
repos_path = f"/tmp/repositories"
if not exists(repos_path):
    makedirs(repos_path)

for csv in listdir("output"):
    df = pd.read_csv("output/" + csv)

    # Cloning repositories and getting a list of LoC sum for each one
    loc_list = clone_n_sum_loc(df, repos_path)

    # Saving new CSV
    df.insert(9, "LoC", value=loc_list, allow_duplicates=True)
    df.to_csv(f"output/loc_{csv}")

l.info("Finished Sprint 01, third step (3/4)")

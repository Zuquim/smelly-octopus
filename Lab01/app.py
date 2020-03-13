from csv import writer
from logging import DEBUG, INFO
from os import getcwd
from os.path import exists
from sys import exit

import pandas as pd

from logzero import setup_logger

from sprints.Lab01S01 import Query as query_01
from sprints.Lab01S02 import Query as query_02

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

# Some constants
_output_path = f"{getcwd()}/output"

# Sprint 01
l.info("Running Sprint 01")
s01 = query_01(url, headers)
s01.run_query()
l.info("Finished Sprint 01")

# Sprint 02
l.info("Running Sprint 02")
s02 = query_02(url, headers)
nodes = s02.json["data"]["search"]["nodes"]
table_headers = nodes[0].keys()
l.info(f"Total nodes after first run: {len(nodes)}")

# Getting nodes for the next 19 pages
for _ in range(1, 20):
    s02.next_page()
    s02.request()
    l.debug(f"Total nodes after last run: {len(nodes)}")
    nodes += s02.json["data"]["search"]["nodes"]
l.info(f"Total nodes after final run: {len(nodes)}")

# Fixing node dictionaries
for i, node in enumerate(nodes):
    nodes[i] = s02.fix_dict(node)
l.info(f"Fixed a total of {len(nodes)} node dictionaries.")

# Saving repositories data to CSV file inside 'output' directory
with open(f"{_output_path}/repositories.csv", "w") as f:
    csv = writer(f)
    csv.writerow(table_headers)
    for repository in nodes:
        l.debug(f"repository={repository}")
        csv.writerow(repository.values())

l.info("Finished Sprint 02")

# Sprint 03
df = pd.read_csv(f"{_output_path}/repositories.csv")
df.keys()

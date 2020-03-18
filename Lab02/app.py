from csv import writer
from logging import DEBUG, INFO
from os import getcwd
from os.path import exists
from sys import exit

from Lab01.sprints.Lab01S02 import Query as query_02

from logzero import setup_logger

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


def first_run(gql_query):
    gql = gql_query
    nodes = gql.json["data"]["search"]["nodes"]
    table_headers = nodes[0].keys()
    l.info(f"Total nodes after first run: {len(nodes)}")
    return gql, table_headers, nodes


def get_me_a_thousand(gql_query, node_list):
    while gql_query.next_page():
        gql_query.request()
        l.debug(f"Total nodes after last run: {len(node_list)}")
        node_list += gql_query.json["data"]["search"]["nodes"]
    l.info(f"Total nodes after final run: {len(node_list)}")
    return gql_query, node_list


def fix_dictionaries(gql_query, node_list):
    for i, node in enumerate(node_list):
        node_list[i] = gql_query.fix_dict(node)
    l.info(f"Fixed a total of {len(node_list)} node dictionaries.")
    return gql_query, node_list


def save_csv(file_name, table_headers, node_list):
    if '.csv' in file_name:
        file_name = file_name[len(file_name)-4:]
    with open(f"{_output_path}/{file_name}.csv", "w") as f:
        csv = writer(f)
        csv.writerow(table_headers)
        for repository in node_list:
            l.debug(f"repository={repository}")
            csv.writerow(repository.values())


# Sprint 01
l.info("Running Sprint 01")

data_template = ("""
{
  search(type: REPOSITORY, query: "user:gvanrossum language:python", after:"!<REPLACE-ME>!", first: 50) {
    repositoryCount
    pageInfo {
      hasNextPage
      endCursor
    }
    nodes {
      ... on Repository {
        name
        url
        stargazers{totalCount}
        watchers{totalCount}
        forkCount
        isFork
        commitComments{totalCount}
        releases{totalCount}
        createdAt
        primaryLanguage {
          name
        }
      }
    }
  }
  rateLimit {
    remaining
    resetAt
  }
}
    """)

# First run
s01 = query_02(url, headers, data_template)
s01, table_headers, nodes = first_run(s01)

# Getting nodes for the next pages
s01, nodes = get_me_a_thousand(s01, nodes)

# Fixing node dictionaries
_, nodes = fix_dictionaries(s01, nodes)

# Saving repositories data to CSV file inside 'output' directory
save_csv("guido_repos", table_headers, nodes)

l.info("Finished Sprint 01, first step (1/4)")

# Step 2
data_template = data_template.replace("user:gvanrossum language", "language")
# First run
s01 = query_02(url, headers, data_template)
s01, table_headers, nodes = first_run(s01)

# Getting nodes for the next pages
s01, nodes = get_me_a_thousand(s01, nodes)

# Fixing node dictionaries
s01, nodes = fix_dictionaries(s01, nodes)

# Saving repositories data to CSV file inside 'output' directory
save_csv("python_repos", table_headers, nodes)

l.info("Finished Sprint 01, second step (2/4)")

# Step 3

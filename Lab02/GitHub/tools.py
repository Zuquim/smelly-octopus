from csv import writer
from datetime import datetime as dt
from logging import DEBUG, INFO
from os import getcwd
from shutil import rmtree
from subprocess import Popen, PIPE

import pandas as pd
from git import Git
from logzero import setup_logger

from .GraphQL import Query

l = setup_logger(name="tools", level=DEBUG)

# Some constants
output_path = f"{getcwd()}/output"

data_template = ("""
{
  search(query: "user:gvanrossum language:python", type: REPOSITORY, first: 50, after:"!<REPLACE-ME>!") {
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


def first_run(gql_query: Query):
    gql = gql_query
    nodes = gql.json["data"]["search"]["nodes"]
    table_headers = nodes[0].keys()
    l.info(f"Total nodes after first run: {len(nodes)}")
    return gql, table_headers, nodes


def get_me_a_thousand(gql_query: Query, node_list: list):
    while gql_query.next_page():
        gql_query.request()
        l.debug(f"Total nodes after last run: {len(node_list)}")
        node_list += gql_query.json["data"]["search"]["nodes"]
    l.info(f"Total nodes after final run: {len(node_list)}")
    return gql_query, node_list


def fix_dictionaries(gql_query: Query, node_list: list):
    for i, node in enumerate(node_list):
        node_list[i] = gql_query.fix_dict(node)
    l.info(f"Fixed a total of {len(node_list)} node dictionaries.")
    return gql_query, node_list


def age_in_seconds(created_at: str, format: str="%Y-%m-%dT%H:%M:%SZ"):
    return dt.today() - dt.strptime(created_at, format)


def save_csv(file_name: str, table_headers: list, node_list: list):
    if '.csv' in file_name:
        file_name = file_name[len(file_name)-4:]
    with open(f"{output_path}/{file_name}.csv", "w") as f:
        csv = writer(f)
        csv.writerow(table_headers)
        for repository in node_list:
            l.debug(f"repository={repository}")
            csv.writerow(repository.values())


def clone_n_sum_loc(name: str, url: str, repos_path: str):
    Git(repos_path).clone(f"{url.replace('https', 'git')}.git")
    l.info(f"Cloned {name}")
    # Analyzing LoC in each repository
    out, err = Popen(
        [
            f"{getcwd()}/../venv/bin/radon",
            "raw",
            # "-O", f"{repos_path}/{name}.txt",
            f"{repos_path}/{name}"
        ], stdout=PIPE, stderr=PIPE
    ).communicate()
    # Checking return code
    if err != b"":
        l.error(err.decode())
        exit(1)

    l.debug(f"Analyzed {name}")
    # Summing total LoC for each repository
    # with open(f"{repos_path}/{name}.txt", "r") as f:
    #     out = f.read()
    loc = 0
    for line in out.decode().splitlines():
        if " LOC:" in line:
            loc += int(line.split(": ")[1])
    l.info(f"LoC for {name}: {loc}")
    rmtree(f"{repos_path}/{name}")
    l.info(f"Removed repository directory ({repos_path}/{name})")


def read_repos_table(file_name: str, repos_path: str, output_path: str=output_path, index: int=0):
    """Clone repositories and sum total LoC for each one."""
    df = pd.read_csv(f"{output_path}/{file_name}")
    loc_list = []
    # Cloning repositories and analyzing LoC
    for i in range(index, len(df["name"])):
        l.info(f"{file_name} | Row #{i}")
        loc = clone_n_sum_loc(df["name"][i], df["url"][i], repos_path)
        loc_list.append(loc)
        # Creating LoC column in case it doesn't already exists
        if "LoC" not in df.columns:
            df.insert(len(df.columns), "LoC", -1)
            df.index = [i for i in range(0, len(df["name"]))]
        l.debug(f"Index={df.index}")
        print(df)
        # Inputing current repository LoC sum to table
        df.loc[:, ("LoC", i)] = loc  # FIXME
        # Saving partial results
        partial_file = f"{output_path}/{file_name.replace('.loc', '')}.loc"
        df.to_csv(partial_file)
        l.debug(f"Saved partial LoC info in {partial_file}")

    # Saving new CSV
    complete_file = f"{output_path}/LoC_{file_name.replace('.loc', '')}"
    df.to_csv(complete_file)
    l.info(f"Saved complete LoC info in {complete_file}")

    return df, loc_list

from csv import writer
from datetime import datetime as dt, timedelta
from logging import DEBUG, INFO
from os import getcwd, listdir, system
from shutil import rmtree
from signal import alarm, signal, SIGALRM
from socket import gethostname
from subprocess import Popen, PIPE

import pandas as pd
from git import Git
from git.exc import GitCommandError
from logzero import setup_logger

from .GraphQL import Query

l = setup_logger(name="tools", level=INFO)

# Some constants
output_path = f"{getcwd()}/output"

data_template = """
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
    """


class TimeoutException(Exception):  # Custom exception class
    pass


def timeout_handler(signum, frame):  # Custom signal handler
    raise TimeoutException


# Change the behavior of SIGALRM
signal(SIGALRM, timeout_handler)


def notify_owner(message: str):
    # Notify code owner via local Telegram Bot script (none provided in project)
    if gethostname() == "heisenberg":
        system(f"st '{message}'")


def sys_cmd(cmd: list) -> str:
    """Execute system commands using subprocess.Popen()."""

    out, err = Popen(cmd, stdout=PIPE, stderr=PIPE).communicate()
    # Checking return code
    if err != b"":
        l.error(err.decode())
        notify_owner(f"Exited(1) ln#80 for: {err.decode()}")
        exit(1)
    else:
        return out.decode()


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


def age_in_seconds(created_at: str, format: str = "%Y-%m-%dT%H:%M:%SZ"):
    return (dt.today() - dt.strptime(created_at, format)).total_seconds()


def save_csv(file_name: str, table_headers: list, node_list: list):
    if ".csv" in file_name:
        file_name = file_name[len(file_name) - 4 :]
    with open(f"{output_path}/{file_name}.csv", "w") as f:
        csv = writer(f)
        csv.writerow(table_headers)
        for repository in node_list:
            l.debug(f"repository={repository}")
            csv.writerow(repository.values())


def remove_directory(path: str, ans: str = "y"):
    print(f"'{path}' content: {listdir(path)}")
    while ans.lower() != "y" and ans.lower() != "n":
        ans = input(f"Remove repository local directory? [y/n] ")
    if ans.lower() == "y":
        rmtree(path)
        l.warning(f"Removed directory at '{path}'")
        return True

    return False


def clone_n_sum_loc(index: int, name: str, url: str, repos_path: str, radon_timeout: int = 1800):
    """Clone Git repository, analyze it using radon raw, calculate and return project LoC."""

    dt_clone = dt.now()
    try:
        Git(repos_path).clone(f"{url.replace('https', 'git')}.git")
    except GitCommandError as e:
        if "Repository not found." in str(e):
            l.error(f"Repository not found!")
            return -404
        elif " already exists and is not an empty directory." in str(e):
            l.warning(f"Repository directory already exists and it's not empty.")
            if remove_directory(f"{repos_path}/{name}"):
                Git(repos_path).clone(f"{url.replace('https', 'git')}.git")
            else:
                l.info("Exiting...")
                notify_owner(f"Exited(0) script ln#150 @ {repos_path}/{name} #{index}")
                exit(0)
        else:
            l.exception(f"Crashed! | {e}")
            notify_owner(f"#{index} | App crashed!")
            exit(1)

    tdelta = str(dt.now() - dt_clone).split('.')[0]
    size = sys_cmd(["du", "-hs", f"{repos_path}/{name}"])
    log_msg = f"#{index} | Cloned: {name} || Size: {size.split()[0]} | Timedelta: {tdelta}"
    l.info(log_msg.replace("||", "|"))
    notify_owner(log_msg.replace(" || ", "\n"))

    # Analyzing LoC in each repository
    dt_radon = dt.now()
    alarm(radon_timeout)  # Setting 30 min timeout for radon analysis
    try:
        out = sys_cmd(
            [
                f"{getcwd()}/../venv/bin/radon",
                "raw",
                # "-O", f"{repos_path}/{name}.txt",
                f"{repos_path}/{name}",
            ]
        )
    except TimeoutException:
        l.error(f"Analysis timeout! Using '-2' as repository LoC.")
        notify_owner(f"#{index} | Analysis timeout for {name}")
        return -2
    else:
        alarm(0)
        tdelta = str(dt.now() - dt_radon).split('.')[0]

    # Summing total LoC for each repository
    # with open(f"{repos_path}/{name}.txt", "r") as f:
    #     out = f.read()
    loc = 0
    for line in out.splitlines():
        if " LOC:" in line:
            loc += int(line.split(": ")[1])
    log_msg = f"#{index} | Analyzed: {name} || LoC: {loc} | Timedelta: {tdelta}"
    l.info(log_msg.replace("||", "|"))
    notify_owner(log_msg.replace(" || ", "\n"))
    rmtree(f"{repos_path}/{name}")
    l.info(f"Removed repository directory ({repos_path}/{name})")

    return loc


def read_repos_table(
    file_name: str, repos_path: str, output_path: str = output_path, index: int = 0
) -> pd.DataFrame:
    """Clone repositories and sum total LoC for each one."""

    df = pd.read_csv(f"{output_path}/{file_name}")

    # Cloning repositories and analyzing LoC
    for i in range(index, len(df["name"])):
        l.info(f"{file_name} | Row #{i}")
        loc = clone_n_sum_loc(i, df["name"][i], df["url"][i], repos_path)
        # Creating LoC column in case it doesn't already exists
        if "LoC" not in df.columns:
            df.insert(len(df.columns), "LoC", -1)
            df.index = [i for i in range(0, len(df["name"]))]
        # Inputing current repository LoC sum to table
        df.at[i, "LoC"] = loc
        # Saving partial results
        partial_file = f"{output_path}/{file_name.replace('.loc', '')}.loc"
        df.to_csv(partial_file)
        l.debug(f"Saved partial LoC info in {partial_file}")

    # Saving new CSV
    complete_file = f"{output_path}/LoC_{file_name.replace('.loc', '')}"
    df.to_csv(complete_file)
    l.info(f"Saved complete LoC info in {complete_file}")
    notify_owner(f"Finished ALL analysis for {complete_file}")

    return df

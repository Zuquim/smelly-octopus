from csv import writer
from logging import DEBUG, INFO
from os import getcwd

from logzero import setup_logger

l = setup_logger(name="tools", level=INFO)

# Some constants
_output_path = f"{getcwd()}/output"

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
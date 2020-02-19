from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL

from logzero import setup_logger
from requests import post

l = setup_logger(name="Lab01S01", level=INFO)


class Query:
    __slots__ = ["response"]

    # GraphQL query definition
    data = {
        "query": """
                {
                  search(query: "stars: >100", type: REPOSITORY, first: 100) {
                    nodes {
                      ... on Repository {
                        nameWithOwner
                        url
                        createdAt
                        updatedAt
                        pullRequests(states: MERGED) {
                          totalCount
                        }
                        releases {
                          totalCount
                        }
                        primaryLanguage{
                          name
                        }
                        totalIssues: issues {
                          totalCount
                        }
                        totalClosedIssues: issues(states: CLOSED) {
                          totalCount
                        }
                      }
                    }
                  }
                }
                """
    }

    def __init__(self, url, headers):
        # Running HTTP POST request
        self.response = post(url, headers=headers, json=self.data)
        l.debug(
            f"response.status_code={self.response.status_code}; "
            f"response.json()='{self.response.json()}'"
        )

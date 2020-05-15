from logging import INFO
from sys import exit
from typing import Optional

from logzero import setup_logger
from requests import post

log = setup_logger(name="GraphQL", level=INFO)

# Request JSON data template
repositories_template = (
    "{"
    "  search("
    '      query:"stars:>100'
    "      language:python"
    '      created:>=2016-01-01",'
    "      type:REPOSITORY,"
    "      first:!<FIRST>!,"
    '      after:"!<AFTER>!"'
    "  ){"
    "    pageInfo{"
    "      hasNextPage"
    "      endCursor"
    "    }"
    "    nodes{"
    "      ... on Repository {"
    "        id"
    "        nameWithOwner"
    "        url"
    "        createdAt"
    "        stargazers { totalCount }"
    "        all_issues: issues{ totalCount } "
    "        closed_issues: issues(states:CLOSED){ totalCount }"
    "      }"
    "    }"
    "  }"
    "  rateLimit{"
    "    remaining"
    "    resetAt"
    "  }"
    "}"
)

issues_template = """
{
  repository(
      owner:"!<OWNER>!",
      name:"!<NAME>!"
    ){
    issues(
        first:!<FIRST>!,
        orderBy:{
          field:CREATED_AT,
          direction:ASC
        },
        after:"!<AFTER>!"
    ){
      pageInfo{
        hasNextPage
        endCursor
      }
      nodes{
        id
        title
        createdAt
        closedAt
        closed
      }
    }    
  }
}
"""

templates = {
    "repositories": repositories_template,
    "issues": issues_template
}


class Query:
    __slots__ = [
        "data",
        "data_template",
        "headers",
        "url",
        "response",
        "json",
        "n_issues",
        "max_per_page",
    ]

    def __init__(
            self,
            url: str,
            headers: dict,
            data_template: str,
            n_issues: int,
            max_per_page: int = 50,
            auto_run: bool = False
    ):
        # Initializing instance attributes
        self.headers = headers
        self.n_issues = n_issues
        self.max_per_page = max_per_page
        self.url = url
        self.json = {}
        self.response = None

        if n_issues < max_per_page:
            self.max_per_page = n_issues

        # Setting up first query (the only one where 'after' is 'null')
        self.data_template = data_template.replace(
            '"!<AFTER>!"', "null").replace("!<FIRST>!", str(self.max_per_page))
        self.data = {"query": self.data_template}

        # Running HTTP POST request
        if auto_run:
            self.request()

    def update_data_template(
            self,
            end_cursor: Optional[str] = None,
            n_issues: Optional[int] = None,
            owner: Optional[str] = None,
            name: Optional[str] = None
    ):
        # Setup repository owner and name for issues query
        if owner and name:
            self.data_template = self.data_template.replace('!<OWNER>!', owner)
            self.data_template = self.data_template.replace('!<NAME>!', name)
            self.data["query"] = self.data_template

        # GraphQL query definition (setting up parameter to get next page)
        if end_cursor:
            self.data_template = self.data_template.replace("!<AFTER>!", end_cursor)
            self.data["query"] = self.data_template

        # Setting node limit
        if n_issues and n_issues < self.max_per_page:
            self.data_template = self.data_template.replace(
                f"first:{self.max_per_page},", f"first:{n_issues},"
            )
            self.data["query"] = self.data_template


        return self.data

    def request(self):
        # Running HTTP POST request
        self.response = post(url=self.url, headers=self.headers, json=self.data)
        log.debug(
            f"response.status_code={self.response.status_code}; "
            f"response.json()='{self.response.json()}'"
        )

        # Checking if request was successful
        if self.noice_response():
            self.json = self.response.json()  # Updating json attribute if True

        return self.response

    def noice_response(self):
        # Checking if HTTP POST request was successful
        if self.response.status_code != 200:
            log.error(
                f"HTTP POST request failed! Status code: "
                f"{self.response.status_code}"
            )
            exit(1)
        if self.response.status_code == 200 and "errors" in self.response.json():
            log.error(
                f"HTTP POST request failed!"
                f"\nErrors:"
                f"\n{[err['message'] for err in self.response.json()['errors']]}"
            )
            exit(1)

        return True

    def next_page(self):
        try:
            if self.json["data"]["search"]["pageInfo"]["hasNextPage"]:
                self.update_data_template(
                    self.json["data"]["search"]["pageInfo"]["endCursor"]
                )
                return self.json["data"]["search"]["pageInfo"]["endCursor"]
            else:
                return False
        except KeyError as e:
            # log.info(f"Doing issues | Exception: {e}")
            if self.json["data"]["repository"]["issues"]["pageInfo"]["hasNextPage"]:
                self.n_issues -= self.max_per_page
                self.update_data_template(
                    end_cursor=self.json["data"]["repository"]["issues"]["pageInfo"]["endCursor"],
                    n_issues=self.n_issues
                )
                return self.json["data"]["repository"]["issues"]["pageInfo"]["endCursor"]
            else:
                return False

    @staticmethod
    def fix_dict(node: dict):
        # Fix request response dictionary
        try:
            node["all_issues"] = node["all_issues"]["totalCount"]
        except KeyError as e:
            log.debug(f"No all_issues | {e}")

        try:
            node["closed_issues"] = node["closed_issues"]["totalCount"]
        except KeyError as e:
            log.debug(f"No closed_issues | {e}")

        try:
            node["stargazers"] = node["stargazers"]["totalCount"]
        except KeyError as e:
            log.debug(f"No stargazers | {e}")

        return node

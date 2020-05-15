from logging import INFO
from sys import exit

from logzero import setup_logger
from requests import post

log = setup_logger(name="GraphQL", level=INFO)

# Request JSON data template
repositories_template = (
    "{"
    "  search("
    '      query: "stars:>100",'
    "      type:REPOSITORY,"
    "      first:50,"
    "      language:python,"
    "      created:>=2016-01-01,"
    '      after:"!<AFTER>!"'
    "  ) {"
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
      owner: "!<OWNER>!",
      name: "!<NAME>!"
    ) {
    issues(
        first: 10,
        orderBy: {
          field: CREATED_AT,
          direction: ASC
        },
        after: "!<AFTER>!"
    ){
      pageInfo{
        hasNextPage
        endCursor
      }
      nodes {
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
    __slots__ = ["data", "data_template", "headers", "url", "response", "json"]

    def __init__(self, url: str, headers: dict, data_template: str):
        # Initializing instance attributes
        self.data = {"query": ""}
        self.data_template = data_template
        self.headers = headers
        self.url = url
        self.json = {}
        self.response = None

        # Setting up first query (the only one where 'after' is 'null')
        self.data["query"] = data_template.replace('"!<AFTER>!"', "null")

        # Running HTTP POST request
        self.request()

    def setup_issues_query(self, owner: str, name: str):
        # Setup repository owner and name for issues query
        self.data["query"] = self.data["query"].replace('"!<OWNER>!"', owner)
        self.data["query"] = self.data["query"].replace('"!<NAME>!"', name)

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

    def new_query(self, end_cursor: str):
        log.debug(f"end_cursor={end_cursor}")

        # GraphQL query definition (setting up parameter to get next page)
        self.data["query"] = self.data_template.replace("!<REPLACE-ME>!", end_cursor)

        return self.data

    def next_page(self):
        try:
            if self.json["data"]["search"]["pageInfo"]["hasNextPage"]:
                self.new_query(self.json["data"]["search"]["pageInfo"]["endCursor"])
                return self.json["data"]["search"]["pageInfo"]["endCursor"]
            else:
                return False
        except KeyError as e:
            log.info(f"Doing issues | Exception: {e}")
            if self.json["data"]["repository"]["issues"]["pageInfo"]["hasNextPage"]:
                self.new_query(
                    self.json["data"]["repository"]["issues"]["pageInfo"]["endCursor"])
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

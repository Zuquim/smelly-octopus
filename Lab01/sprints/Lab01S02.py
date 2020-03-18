from logging import DEBUG, INFO
from sys import exit

from logzero import setup_logger
from requests import post

l = setup_logger(name="Lab01S02", level=INFO)


class Query:
    __slots__ = ["data", "data_template", "headers", "url", "response", "json"]

    # Request JSON data template
    default_template = (
        "{"
        "  search("
        '      query:"stars:>100",'
        "      type:REPOSITORY,"
        "      first:50,"
        '      after:"!<REPLACE-ME>!"){'
        "    pageInfo{"
        "      hasNextPage"
        "      endCursor"
        "    }"
        "    nodes{"
        "      ... on Repository {"
        "        nameWithOwner"
        "        url"
        "        createdAt"
        "        updatedAt"
        "        primaryLanguage{ name }"
        "        releases{ totalCount }"
        "        pullRequests{ totalCount }"
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

    def __init__(self, url, headers, data_template=default_template):
        # Initializing instance attributes
        self.data = {"query": ""}
        self.data_template = data_template
        self.headers = headers
        self.url = url
        self.json = {}

        # Setting up first query (the only one where 'after' is 'null')
        self.data["query"] = data_template.replace('"!<REPLACE-ME>!"', "null")

        # Running HTTP POST request
        self.request()

    def request(self):
        # Running HTTP POST request
        self.response = post(url=self.url, headers=self.headers, json=self.data)
        l.debug(
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
            l.error(
                f"HTTP POST request failed! Status code: "
                f"{self.response.status_code}"
            )
            exit(1)
        if self.response.status_code == 200 and "errors" in self.response.json():
            l.error(
                f"HTTP POST request failed!"
                f"\nErrors:"
                f"\n{[err['message'] for err in self.response.json()['errors']]}"
            )
            exit(1)

        return True

    def new_query(self, end_cursor):
        l.debug(f"end_cursor={end_cursor}")

        # GraphQL query definition (setting up parameter to get next page)
        self.data["query"] = self.data_template.replace("!<REPLACE-ME>!", end_cursor)

        return self.data

    def next_page(self):
        if self.json["data"]["search"]["pageInfo"]["hasNextPage"]:
            self.new_query(self.json["data"]["search"]["pageInfo"]["endCursor"])
            return self.json["data"]["search"]["pageInfo"]["endCursor"]
        else:
            return False

    def fix_dict(self, node):
        try:
            node["primaryLanguage"] = node["primaryLanguage"]["name"]
        except TypeError as e:
            l.warning(f"Primary language not available. Setting null. | {e}")
            node["primaryLanguage"] = None
        except KeyError as e:
            l.debug(f"No primaryLanguage | {e}")
        try:
            node["releases"] = node["releases"]["totalCount"]
        except KeyError as e:
            l.debug(f"No releases | {e}")
        try:
            node["pullRequests"] = node["pullRequests"]["totalCount"]
        except KeyError as e:
            l.debug(f"No pullRequests | {e}")
        try:
            node["all_issues"] = node["all_issues"]["totalCount"]
        except KeyError as e:
            l.debug(f"No all_issues | {e}")
        try:
            node["closed_issues"] = node["closed_issues"]["totalCount"]
        except KeyError as e:
            l.debug(f"No closed_issues | {e}")
        try:
            node["stargazers"] = node["stargazers"]["totalCount"]
        except KeyError as e:
            l.debug(f"No stargazers | {e}")
        try:
            node["watchers"] = node["watchers"]["totalCount"]
        except KeyError as e:
            l.debug(f"No watchers | {e}")
        try:
            node["commitComments"] = node["commitComments"]["totalCount"]
        except KeyError as e:
            l.debug(f"No commitComments | {e}")
        return node

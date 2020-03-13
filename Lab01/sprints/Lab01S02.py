from logging import DEBUG, INFO

from logzero import setup_logger
from requests import post

l = setup_logger(name="Lab01S02", level=INFO)


class Query:
    __slots__ = ["data", "headers", "url", "response", "json"]

    # Request JSON data template
    data_template = (
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

    def __init__(self, url, headers):
        # Initializing instance attributes
        self.data = {"query": ""}
        self.headers = headers
        self.url = url
        self.json = {}

        # Setting up first query (the only one where 'after' is 'null')
        self.data["query"] = self.data_template.replace('"!<REPLACE-ME>!"', "null")

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
        self.new_query(self.json["data"]["search"]["pageInfo"]["endCursor"])

        return self.json["data"]["search"]["pageInfo"]["endCursor"]

    def fix_dict(self, node):
        try:
            node["primaryLanguage"] = node["primaryLanguage"]["name"]
        except TypeError as e:
            l.warning(f"Primary language not available. Setting null. | {e}")
            node["primaryLanguage"] = None
        node["releases"] = node["releases"]["totalCount"]
        node["pullRequests"] = node["pullRequests"]["totalCount"]
        node["all_issues"] = node["all_issues"]["totalCount"]
        node["closed_issues"] = node["closed_issues"]["totalCount"]
        return node

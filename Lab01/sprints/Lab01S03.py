from logging import DEBUG, INFO

from logzero import setup_logger
from requests import post

from .Lab01S02 import Query

l = setup_logger(name="Lab01S03", level=INFO)


class Repository:
    __slots__ = [
        "owner",
        "name",
        "url",
        "created",
        "updated",
        "primary_language",
        "releases",
        "pull_requests",
        "total_issues",
        "closed_issues",
    ]

    def __init__(
            self,
            owner_slash_name,
            url,
            created,
            updated,
            primary_language=None,
            releases=0,
            pull_requests=0,
            total_issues=0,
            closed_issues=0
    ):
        self.owner = owner_slash_name.split("/")[1]
        self.name = owner_slash_name.split("/")[0]
        self.url = url
        self.created = created
        self.updated = updated
        self.primary_language = primary_language
        self.releases = releases
        self.pull_requests = pull_requests
        self.total_issues = total_issues
        self.closed_issues = closed_issues

        # Setting up first query (the only one where 'after' is 'null')
        self.data["query"] = self.data_template.replace('"!<REPLACE-ME>!"', "null")

        # Running HTTP POST request
        self.request()

    def __repr__(self):
        pass

    def __str__(self):
        pass

    def __dict__(self):
        return {
            "owner": self.owner,
            "name": self.name,
            "url": self.url,
            "created": self.created,
            "updated": self.updated,
            "primary language": self.primary_language,
            "release": self.releases,
            "pull request": self.pull_requests,
            "total issues": self.total_issues,
            "closed issues": self.closed_issues,
        }

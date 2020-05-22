from typing import List, Tuple


class StackSearchAdvanced:
    __slots__ = [
        "backoff",
        "has_more",
        "page",
        "quota_max",
        "quota_remaining",
        "total",
        "items",
    ]

    def __init__(self, response: dict):
        self.backoff: bool = response["backoff"]
        self.has_more: bool = response["has_more"]
        self.page: int = response["page"]
        self.quota_max: int = response["quota_max"]
        self.quota_remaining: int = response["quota_remaining"]
        self.total: int = response["total"]
        self.items: list = []
        [self.items.append(self.Item(i)) for i in response["items"]]

    def headers(self) -> Tuple[str, str, str, str, str, str, str]:
        return (
            "backoff",
            "has_more",
            "page",
            "quota_max",
            "quota_remaining",
            "total",
            "items",
        )

    class Item:
        __slots__ = [
            "owner",
            "question_id",
            "tags",
            "is_answered",
            "answer_count",
            "view_count",
            "score",
            "last_activity_date",
            "creation_date",
            "title",
            "link",
        ]

        def __init__(self, content: dict):
            # self.owner: dict = content["owner"]
            self.question_id: int = content["question_id"]
            self.tags: list = content["tags"]
            self.is_answered: bool = content["is_answered"]
            self.answer_count: int = content["answer_count"]
            self.view_count: int = content["view_count"]
            self.score: int = content["score"]
            self.last_activity_date: str = content["last_activity_date"]
            self.creation_date: str = content["creation_date"]
            self.title: str = content["title"]
            self.link: str = content["link"]

        def headers(
            self,
        ) -> Tuple[str, str, str, str, str, str, str, str, str, str]:
            return (
                # "owner",
                "question_id",
                "tags",
                "is_answered",
                "answer_count",
                "view_count",
                "score",
                "last_activity_date",
                "creation_date",
                "title",
                "link",
            )

        def to_tuple(
                self
        ) -> Tuple[int, list, bool, int, int, int, str, str, str, str]:
            return (
                # self.owner,
                self.question_id,
                self.tags,
                self.is_answered,
                self.answer_count,
                self.view_count,
                self.score,
                self.last_activity_date,
                self.creation_date,
                self.title,
                self.link,
            )

    def to_tuple(self) -> Tuple[bool, bool, int, int, int, int, List[Item]]:
        return (
            self.backoff,
            self.has_more,
            self.page,
            self.quota_max,
            self.quota_remaining,
            self.total,
            self.items,
        )

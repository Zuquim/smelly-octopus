from json import dump

import pandas as pd
from logzero import logger as log
from stackapi import StackAPI


def main():
    # Loading GitHub issues
    df = pd.read_csv("artifacts/issues.csv")
    issue_titles = df["title"].to_list()
    # issue_titles = list(dict.fromkeys(issue_titles))

    stack_api = StackAPI("stackoverflow")

    issue_questions = []
    for i, title in enumerate(issue_titles):
        if len(title.split()) > 3:
            log.info(f'#{i}\tfetching questions for issue: "{title}"')
            issue_questions.append(stack_api.fetch(
                "search/advanced",
                title=title,
                tagged=["python"],
                fromdate="2016-01-01",
                order="desc",
                sort="votes",
                pagesize=100,
                page=1
            ))
        else:
            log.warning(f'#{i}\tissue title is too small: "{title}"')

    for i, i_q in zip(df["id"], issue_questions):
        issue, questions = i_q
        log.info(f"#{i}\tSaving questions for issue: {issue}")
        with open(f"output/{issue}.json", "w", encoding="utf-8") as f:
            dump(questions, f, indent=2)


if __name__ == "__main__":
    main()
    log.info("Done!")

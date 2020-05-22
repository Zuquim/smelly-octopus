from csv import DictWriter
from json import dump
from os import listdir, makedirs
from os.path import exists
from time import sleep, time

import pandas as pd
from logzero import logger as log
from stackapi import StackAPI

from model import StackSearchAdvanced


def main():
    stack_api = StackAPI("stackoverflow")
    # stack_api = StackAPI("stackoverflow", key="wDmtc8eJ*y5wJ)7)VyN5ww((", access_token="")

    issues_per_repos = listdir("output")
    issues_per_repos.remove("repositories.csv")
    to_remove = []
    for file_ in issues_per_repos:
        if not file_.endswith(".csv"):
            to_remove.append(file_)
    for i in to_remove:
        issues_per_repos.remove(i)
    for j, csv_file in enumerate(issues_per_repos):
        # Reading repository's issues CSV
        df = pd.read_csv(f"output/{csv_file}", delimiter="", engine="python")
        owner_repos = csv_file.replace("_issues.csv", "").split("_")
        owner_repos = f"{owner_repos[0]}/{'_'.join(owner_repos[1:])}"

        # Checking if directory exists (which means it was already queried)
        repos_path = f"output/{owner_repos}"
        if exists(repos_path):
            log.warning(f"#{j}/{len(issues_per_repos)}\tSkipping {owner_repos}")
            continue

        makedirs(repos_path)
        counter = 0
        log.info(
            f"#{j}/{len(issues_per_repos)}\tReading issues for {owner_repos}"
        )
        for id_, title in zip(df["id"], df["title"]):
            counter += 1
            if type(title) is float:
                log.error(f"csv={csv_file}")
                continue
            if len(title.split()) > 3:
                start_time = time()
                log.info(
                    f'#{counter}/{len(df)}\tFetching questions for issue: "{title}"'
                )
                issue_questions = {
                    id_: stack_api.fetch(
                        "search/advanced",
                        # body=title,
                        title=title,
                        tagged=["python", owner_repos.split("/")[1]],
                        order="desc",
                        sort="votes",
                        min=0,
                        pagesize=10,
                        page=1
                    )
                }
                log.debug(
                    f"________Quota remaining:\t"
                    f"{issue_questions[id_]['quota_remaining']}/{issue_questions[id_]['quota_max']}"
                    f"\t| backoff={issue_questions[id_]['backoff']}"
                )
                sleep(1)
            else:
                log.warning(
                    f'#{counter}/{len(df)}\tIssue title is too small: "{title}"'
                )
                continue

            # Checking backoff:
            if issue_questions[id_]["backoff"]:
                log.warning(f"---- Back off ----")
                sleep(60)

            questions_path = f"{csv_file.replace('_issues.csv', '_questions.csv')}"
            if issue_questions[id_]["total"] > 0:
                if not exists(questions_path):
                    ssa = StackSearchAdvanced(issue_questions[id_])
                    ssa.to_csv(f"output/{questions_path}")
                else:
                    with open(f"output/{questions_path}", "r", encoding="utf-8") as f:
                        if str(issue_questions[id_]["items"][0]["question_id"]) in f.read():
                            log.warning(
                                f"#{counter}/{len(df)}\tQuestions already saved."
                            )
                            continue
            else:
                log.warning(f"#{counter}/{len(df)}\tNo questions found.")
                continue

            # Appending questions CSV
            ssa = StackSearchAdvanced(issue_questions[id_])
            ssa.to_csv(f"output/{questions_path}")

            # Saving questions JSON
            with open(f"{repos_path}/{id_}.json", "w", encoding="utf-8") as f:
                dump(issue_questions, f, indent=2)

            log.debug(f"Done in {int(time() - start_time - 1)} seconds.")


if __name__ == "__main__":
    start_time_main = time()
    main()
    log.info(f"All done in {int(time() - start_time_main)} seconds.")

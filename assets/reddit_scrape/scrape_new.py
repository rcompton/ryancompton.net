import os
import time
import datetime
import logging

import pandas as pd
import praw
import sqlalchemy

logging.basicConfig(level=logging.DEBUG)

# conn = sqlalchemy.create_engine('sqlite:////home/aahu/Dropbox/ryancompton.net/assets/reddit_scrape/scores.db')
# conn.connect()

cols = sorted(
    set(
        [
            "subreddit",
            "title",
            "ups",
            "score",
            "downs",
            "domain",
            "url",
            "num_reports",
            "stickied",
            "permalink",
            "over_18",
            "mod_reports",
            "locked",
            "hidden",
            "distinguished",
            "banned_by",
            "created",
            "edited",
            "from",
            "from_id",
            "from_kind",
            "link_flair_text",
            "approved_by",
            "archived",
            "author",
            "author_flair_text",
            "id",
            "gilded",
            "hide_score",
            "user_reports",
            "created_utc",
            "likes",
            "subreddit_id",
            "selftext",
            "selftext_html",
            "removal_reason",
            "report_reasons",
            "thumbnail",
            "quarantine",
            "name",
            "num_comments",
        ]
    )
)


def login():
    username = os.environ["RUSER"]
    passw = os.environ["RPASS"]
    r = praw.Reddit(user_agent="get new submissions")
    r.login(username=username, password=passw)
    return r


def main():
    r = login()
    subreddit_names = [
        "news",
        "politics",
        "worldnews",
        "aww",
        "askreddit",
        "todayilearned",
        "science",
        "IAmA",
        "music",
        "gifs",
        "the_donald",
        "PoliticalDiscussion",
        "Conservative",
        "announcements",
        "videos",
        "gaming",
        "movies",
        "art",
        "WikiLeaks",
        "DNCLeaks",
        "4chan",
        "pics",
        "worldpolitics",
        "television",
        "space",
        "food",
        "listentothis",
        "inthenews",
        "funny",
        "hillaryclinton",
        "enoughtrumpspam",
        "europe",
        "games",
        "conspiracy",
        "Protectandserve",
        "Socialism",
    ]
    subreddit_names = set(subreddit_names)
    while True:
        for subreddit_name in subreddit_names:
            try:
                time.sleep(5)
                subreddit = r.get_subreddit(subreddit_name)
                submissions = subreddit.get_new(limit=None)
                sub_dics = [s.__dict__ for s in submissions]
                df = pd.DataFrame(sub_dics)
                df2 = df[cols].copy()
                df2["subreddit"] = df2["subreddit"].map(str)
                df2["user_reports"] = df2["user_reports"].map(str)
                df2["report_reasons"] = df2["report_reasons"].map(str)
                df2["author"] = df2["author"].map(str)
                df2["approved_by"] = df2["approved_by"].map(str)
                df2["mod_reports"] = df2["mod_reports"].map(str)
                df2["fetch_time"] = df.index.map(lambda x: datetime.datetime.now())
                df2["edited"] = df2["edited"].map(int)
                df2.to_gbq(
                    "reddit_scores.submissions",
                    "bigquery-reddit-1003",
                    if_exists="append",
                )
                # df2.to_sql('submissions', conn, if_exists='append')
                # cnt = conn.execute('SELECT COUNT(*) FROM submissions;').fetchall()[0][0]
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                logging.exception("meh")
        time.sleep(1)


if __name__ == "__main__":
    main()

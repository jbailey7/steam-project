import sys
from datetime import datetime, timedelta
from airflow.sdk import dag, task
from api import get_top_games, get_news, get_stats
from database import store_dataframe, list_tables

# Make sure Airflow can import your project code
PROJECT_DIR = "/opt/airflow/steam_project"
if PROJECT_DIR not in sys.path:
    sys.path.append(PROJECT_DIR)

# airflow metadata
DEFAULT_ARGS = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}

# defining the DAG
@dag(
    dag_id="steam_etl",
    default_args=DEFAULT_ARGS,
    description="Fetch Steam top games/news/stats and load into SQLite",
    schedule_interval="None", # no scheduld runs, only manual for now
    tags=["steam"],
)

# defines tasks
def steam_etl():
    """
    ETL pipeline broken into multiple tasks:

    1. fetch_top_games              -> dict of {game_name: appid}
    2. fetch_and_store_news(games)  -> writes 'news' table
    3. fetch_and_store_stats(games) -> writes 'stats' table
    4. log_tables()                 -> prints current tables
    """

    @task()
    def fetch_top_games_task(limit: int = 100) -> dict:
        """
        Call api.get_top_games() and return the dict of {name: appid}.
        """
        games = get_top_games(limit=limit)
        print(f"Fetched {len(games)} top games.")
        return games

    @task()
    def fetch_and_store_news(games: dict) -> int:
        """
        Use api.get_news(games) and store results into the 'news' table.
        """
        news_df = get_news(games)
        store_dataframe(news_df, "news")
        row_count = len(news_df)
        print(f"Wrote {row_count} rows to 'news' table.")
        return row_count

    @task()
    def fetch_and_store_stats(games: dict) -> int:
        """
        Use api.get_stats(games) and store results into the 'stats' table.
        """
        stats_df = get_stats(games)
        store_dataframe(stats_df, "stats")
        row_count = len(stats_df)
        print(f"Wrote {row_count} rows to 'stats' table.")
        return row_count

    @task()
    def log_tables_task() -> list:
        """
        Log the current tables in the SQLite DB.
        """
        tables = list_tables()
        print(f"Current tables in DB: {tables}")
        return tables

    games = fetch_top_games_task()

    # because fetch_and_store_news and fetch_and_store_stats both have games as an arg, they are dependent on fetch_top_games_task
    news_rows = fetch_and_store_news(games)
    stats_rows = fetch_and_store_stats(games)

    # Ensure logging runs after both newes and stats are written
    log = log_tables_task()
    [news_rows, stats_rows] >> log


# Instantiate DAG for Airflow to pick up
steam_etl_dag = steam_etl()

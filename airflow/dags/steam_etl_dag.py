import sys
from datetime import datetime, timedelta
from airflow.decorators import dag, task

# Make sure Airflow can import your project code
PROJECT_DIR = "/opt/airflow/steam_project"
if PROJECT_DIR not in sys.path:
    sys.path.append(PROJECT_DIR)

from api import get_top_games, get_news, get_stats
from database import store_dataframe, list_tables


DEFAULT_ARGS = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


@dag(
    dag_id="steam_etl",
    default_args=DEFAULT_ARGS,
    description="Fetch Steam top games/news/stats and load into SQLite",
    schedule=None,  # manual only – no automatic scheduling
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["steam"],
)
def steam_etl():
    """
    ETL pipeline broken into multiple tasks:

    1. fetch_top_games  -> dict of {game_name: appid}
    2. fetch_and_store_news(games)  -> writes 'news' table
    3. fetch_and_store_stats(games) -> writes 'stats' table
    4. log_tables()                 -> prints current tables
    """

    @task()
    def fetch_top_games_task(limit: int = 100) -> dict:
        games = get_top_games(limit=limit)
        print(f"Fetched {len(games)} top games.")
        return games

    @task()
    def fetch_and_store_news(games: dict) -> int:
        news_df = get_news(games)
        store_dataframe(news_df, "news")
        row_count = len(news_df)
        print(f"Wrote {row_count} rows to 'news' table.")
        return row_count

    @task()
    def fetch_and_store_stats(games: dict) -> int:
        stats_df = get_stats(games)
        store_dataframe(stats_df, "stats")
        row_count = len(stats_df)
        print(f"Wrote {row_count} rows to 'stats' table.")
        return row_count

    @task()
    def log_tables_task() -> list:
        tables = list_tables()
        print(f"Current tables in DB: {tables}")
        return tables

    # Wire the flow
    games = fetch_top_games_task()
    news_rows = fetch_and_store_news(games)
    stats_rows = fetch_and_store_stats(games)

    log = log_tables_task()
    [news_rows, stats_rows] >> log


# Instantiate DAG for Airflow to pick up
steam_etl_dag = steam_etl()

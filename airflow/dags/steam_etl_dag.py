import os
import sys
from datetime import datetime, timedelta

from airflow.decorators import dag, task

# From docker-compose, project is mounted at /opt/airflow/steam_project
sys.path.append("/opt/airflow/steam_project")

from src.api import (
    get_ban_info,
    get_current_players,
    get_news,
    get_owned_games,
    get_stats,
    get_steam_level,
    get_steam_user_info,
    get_store_info,
    get_top_games,
)

DEFAULT_ARGS = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

TOP_GAMES_LIMIT = 25

'''
DAG 1
- steam_user_lookup_dag
- sync a single user's profile, owned games, level, and ban info.
'''
@dag(
    dag_id="steam_user_lookup_dag",
    default_args=DEFAULT_ARGS,
    schedule=None,  # manual only – no automatic scheduling
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["steam", "user", "dashboard"],
)
def steam_user_lookup_dag():

    # get STEAM_API_KEY and DEFAULT_STEAM_ID
    @task
    def load_config():
        api_key = os.getenv("STEAM_API_KEY")
        steam_id = os.getenv("DEFAULT_STEAM_ID")

        if not api_key:
            raise ValueError("STEAM_API_KEY environment variable not set")
        if not steam_id:
            raise ValueError("DEFAULT_STEAM_ID environment variable not set")

        return {"api_key": api_key, "steam_id": steam_id}

    # get_steam_user_info (writes to DB)
    @task
    def fetch_user_profile(cfg: dict):
        api_key = cfg["api_key"]
        steam_id = cfg["steam_id"]

        df = get_steam_user_info(steam_id, api_key)
        print(
            f"[user_profile] steam_id={steam_id}, "
            f"rows={len(df) if hasattr(df, 'shape') else 'N/A'}"
        )
        return steam_id

    # get_owned_games (writes to DB)
    @task
    def fetch_owned_games(cfg: dict):
        api_key = cfg["api_key"]
        steam_id = cfg["steam_id"]

        owned = get_owned_games(api_key, steam_id)
        game_count = owned.get("response", {}).get("game_count", 0)
        print(f"[owned_games] steam_id={steam_id}, game_count={game_count}")
        return {"steam_id": steam_id, "game_count": game_count}

    # get_steam_level 
    @task
    def fetch_user_level(cfg: dict):
        api_key = cfg["api_key"]
        steam_id = cfg["steam_id"]

        level = get_steam_level(api_key, steam_id)
        print(f"[user_level] steam_id={steam_id}, response={level}")
        return level

    # get_ban_info
    @task
    def fetch_user_bans(cfg: dict):
        api_key = cfg["api_key"]
        steam_id = cfg["steam_id"]

        bans = get_ban_info(api_key, steam_id)
        print(f"[user_bans] steam_id={steam_id}, response={bans}")
        return bans

    @task
    def summarize_dag1(
        profile_steam_id: str,
        owned_info: dict,
        level_info: dict,
        bans_info: dict,
    ):
        print(f"Profile steam_id: {profile_steam_id}")
        print(f"Owned games info: {owned_info}")
        print(f"Level response: {level_info}")
        print(f"Ban response: {bans_info}")

    cfg = load_config()
    profile_id = fetch_user_profile(cfg)
    owned_info = fetch_owned_games(cfg)
    level_info = fetch_user_level(cfg)
    bans_info = fetch_user_bans(cfg)

    summarize_dag1(
        profile_steam_id=profile_id,
        owned_info=owned_info,
        level_info=level_info,
        bans_info=bans_info,
    )


steam_user_lookup = steam_user_lookup_dag()



"""
DAG 2
- steam_game_explorer_dag
- For the top N games, refresh news, achievement stats, store metadata, and current player counts.
"""
@dag(
    dag_id="steam_game_explorer_dag",
    default_args=DEFAULT_ARGS,
    schedule=None,  # manual only – no automatic scheduling
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["steam", "games", "news", "stats", "dashboard"],
)
def steam_game_explorer_dag():

    # get_top_games (writes 'games' table)
    @task
    def fetch_top_games(limit: int = TOP_GAMES_LIMIT) -> dict:
        games = get_top_games(limit=limit)
        print(f"[top_games] fetched={len(games)}")
        return games  # {name: appid}

    # extract list of appids
    @task
    def extract_appids(games: dict) -> list:
        appids = list(games.values())
        print(f"[extract_appids] appids={appids}")
        return appids

    # writes news - per app
    @task
    def refresh_news_for_app(appid: int):
        df = get_news(appid)
        print(
            f"[news] appid={appid}, rows={len(df) if hasattr(df, 'shape') else 0}"
        )
        return appid

    # writes stats - per app
    @task
    def refresh_stats_for_app(appid: int):
        df = get_stats(appid)
        print(
            f"[stats] appid={appid}, rows={len(df) if hasattr(df, 'shape') else 0}"
        )
        return appid

    # writes store data - per app
    @task
    def refresh_store_for_app(appid: int):
        info = get_store_info(appid)
        print(f"[store] appid={appid}, has_data={bool(info)}")
        return appid

    # write player counts - per app
    @task
    def refresh_players_for_app(appid: int):
        count = get_current_players(appid)
        print(f"[players] appid={appid}, count={count}")
        return appid

    @task
    def summarize_game_explorer(
        news_appids: list,
        stats_appids: list,
        store_appids: list,
        players_appids: list,
    ):
        print(f"News refreshed for appids: {news_appids}")
        print(f"Stats refreshed for appids: {stats_appids}")
        print(f"Store info refreshed for appids: {store_appids}")
        print(f"Player counts refreshed for appids: {players_appids}")

    games = fetch_top_games()
    appids = extract_appids(games)

    # Dynamic task mapping per appid
    news_appids = refresh_news_for_app.expand(appid=appids)
    stats_appids = refresh_stats_for_app.expand(appid=appids)
    store_appids = refresh_store_for_app.expand(appid=appids)
    players_appids = refresh_players_for_app.expand(appid=appids)

    summarize_game_explorer(
        news_appids=news_appids,
        stats_appids=stats_appids,
        store_appids=store_appids,
        players_appids=players_appids,
    )


steam_game_explorer = steam_game_explorer_dag()


"""
DAG 3
- steam_global_metrics_dag
- For the top N games, ensure store metadata and player counts are fresh for the "Global Metrics" dashboard view.
"""
@dag(
    dag_id="steam_global_metrics_dag",
    default_args=DEFAULT_ARGS,
    schedule=None,  # manual only – no automatic scheduling
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["steam", "metrics", "dashboard"],
)
def steam_global_metrics_dag():
    # get_top_games
    @task
    def fetch_top_games_metrics(limit: int = TOP_GAMES_LIMIT) -> dict:
        games = get_top_games(limit=limit)
        print(f"[metrics_top_games] fetched={len(games)}")
        return games

    # extract list of appids
    @task
    def extract_appids_metrics(games: dict) -> list:
        appids = list(games.values())
        print(f"[metrics_extract_appids] appids={appids}")
        return appids

    # store metadata (per app)
    @task
    def refresh_store_for_metrics(appid: int):
        info = get_store_info(appid)
        print(f"[metrics_store] appid={appid}, has_data={bool(info)}")
        return appid
    
    # store player counts (per app)
    @task
    def refresh_players_for_metrics(appid: int):
        count = get_current_players(appid)
        print(f"[metrics_players] appid={appid}, count={count}")
        return appid

    @task
    def summarize_global_metrics(store_appids: list, players_appids: list):
        print("=== Global Metrics Summary ===")
        print(f"Store metadata refreshed for appids: {store_appids}")
        print(f"Player counts refreshed for appids: {players_appids}")
        print("================================")

    games = fetch_top_games_metrics()
    appids = extract_appids_metrics(games)

    store_appids = refresh_store_for_metrics.expand(appid=appids)
    players_appids = refresh_players_for_metrics.expand(appid=appids)

    summarize_global_metrics(
        store_appids=store_appids,
        players_appids=players_appids,
    )


steam_global_metrics = steam_global_metrics_dag()
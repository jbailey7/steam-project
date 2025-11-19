import json
import sqlite3
import pandas as pd
from contextlib import closing

DB_PATH = os.getenv("STEAM_DB_PATH", "steam.db")


def create_connection():
    """Create a SQLite database connection."""
    conn = sqlite3.connect(DB_PATH)
    return conn


def store_dataframe(df, table_name, if_exists="replace"):
    """Store a pandas DataFrame in the database."""
    if df.empty:
        print(f"No data to store for {table_name}")
        return

    conn = create_connection()
    df.to_sql(table_name, conn, if_exists=if_exists, index=False)
    conn.close()
    print(f"Stored {len(df)} records in '{table_name}' table.")


def load_table(table_name):
    """Load a table back into a DataFrame."""
    conn = create_connection()
    df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    conn.close()
    return df


def list_tables():
    """Show available tables in the database."""
    conn = create_connection()
    tables = pd.read_sql_query(
        "SELECT name FROM sqlite_master WHERE type='table';", conn
    )
    conn.close()
    return tables["name"].tolist()


def store_steamspy_table(df):
    """Store SteamSpy data into steam.db as table 'games'."""
    store_dataframe(df, "games")


def store_store_info(appid, info):
    """Persist Store metadata for a single appid."""
    if not info:
        print(f"No store metadata to store for appid {appid}")
        return

    price = info.get("price_overview") or {}
    record = {
        "appid": appid,
        "name": info.get("name"),
        "type": info.get("type"),
        "is_free": info.get("is_free"),
        "release_date": info.get("release_date", {}).get("date"),
        "price_currency": price.get("currency"),
        "price_final": None if price.get("final") is None else price.get("final") / 100.0,
        "price_discount_percent": price.get("discount_percent"),
        "raw_json": json.dumps(info)
    }

    conn = create_connection()
    try:
        with closing(conn.cursor()) as cur:
            cur.execute("DELETE FROM store_metadata WHERE appid=?", (appid,))
            conn.commit()
    except sqlite3.OperationalError:
        pass
    pd.DataFrame([record]).to_sql("store_metadata", conn, if_exists="append", index=False)
    conn.close()
    print(f"Stored store metadata for appid {appid}")


def store_player_count(appid, player_count):
    """Persist the latest concurrent player count for an app."""
    if player_count is None:
        print(f"No player count to store for appid {appid}")
        return

    df = pd.DataFrame([{
        "appid": appid,
        "player_count": player_count,
        "retrieved_at": pd.Timestamp.utcnow()
    }])
    conn = create_connection()
    try:
        with closing(conn.cursor()) as cur:
            cur.execute("DELETE FROM player_counts WHERE appid=?", (appid,))
            conn.commit()
    except sqlite3.OperationalError:
        pass
    df.to_sql("player_counts", conn, if_exists="append", index=False)
    conn.close()
    print(f"Stored player count for appid {appid}")


def store_user_profile(df):
    """Persist Steam user profile summary rows."""
    if df.empty:
        print("No user profile data to store")
        return
    steamid = df.iloc[0]["steamid"]
    conn = create_connection()
    try:
        with closing(conn.cursor()) as cur:
            cur.execute("DELETE FROM user_profiles WHERE steamid=?", (steamid,))
            conn.commit()
    except sqlite3.OperationalError:
        pass
    df.to_sql("user_profiles", conn, if_exists="append", index=False)
    conn.close()
    print(f"Stored user profile for steamid {steamid}")


def store_owned_games(steam_id, owned_json):
    """Persist owned games for a Steam user."""
    games = owned_json.get("response", {}).get("games", [])
    if not games:
        print(f"No owned games to store for steamid {steam_id}")
        return

    df = pd.DataFrame(games)
    df["steamid"] = steam_id

    conn = create_connection()
    try:
        with closing(conn.cursor()) as cur:
            cur.execute("DELETE FROM owned_games WHERE steamid=?", (steam_id,))
            conn.commit()
    except sqlite3.OperationalError:
        pass
    df.to_sql("owned_games", conn, if_exists="append", index=False)
    conn.close()
    print(f"Stored {len(df)} owned games for steamid {steam_id}")

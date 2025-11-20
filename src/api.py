import requests
import pandas as pd

from .database import (
    store_store_info,
    store_player_count,
    store_user_profile,
    store_owned_games,
    store_dataframe,
)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9"
}

# Utility – Safe JSON fetch
def _safe_json(url, timeout=10):
    try:
        r = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout, proxies=None)
        r.raise_for_status()
        return r.json()

    except requests.exceptions.Timeout:
        print(f"Timeout in _safe_json while fetching {url} (timeout={timeout}s)")
        return {}

    except requests.exceptions.RequestException as e:
        print(f"Error in _safe_json while fetching {url}: {e}")
        return {}

    except ValueError as e:
        # JSON decoding errors
        print(f"JSON decode error in _safe_json for {url}: {e}")
        return {}

# 1. Global: Top Games
def get_top_games(limit=100):
    """Return dict: {game_name: appid} using SteamCharts API + Store API."""
    url = "https://api.steampowered.com/ISteamChartsService/GetMostPlayedGames/v1/"
    data = _safe_json(url)

    ranks = data.get("response", {}).get("ranks", [])
    ranks = ranks[:limit]

    games = {}

    for g in ranks:
        appid = g.get("appid")
        if not appid:
            continue

        # Fetch real game name using Store API
        store_raw = _safe_json(f"https://store.steampowered.com/api/appdetails?appids={appid}")
        block = store_raw.get(str(appid), {})

        if not block.get("success"):
            continue

        dat = block.get("data", {})
        if not dat:
            continue

        name = dat.get("name", f"App {appid}")
        games[name] = appid
        
    # write to database
    df = pd.DataFrame([games])
    store_dataframe(df, "games", if_exists="append")

    return games

# 2. Global: News
def get_news(appid):
    """Return a DataFrame of recent news for a single appid."""
    url = f"https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/?appid={appid}&count=20&format=json"
    data = _safe_json(url)

    items = data.get("appnews", {}).get("newsitems", [])
    df = pd.DataFrame(items)

    if not df.empty:
        df["date"] = pd.to_datetime(df["date"], unit="s", errors="coerce")
        df["appid"] = appid
        store_dataframe(df, "news", if_exists="append")

    return df

# 3. Global: Achievement Stats
def get_stats(appid):
    """Return DataFrame of global achievement percentages for a single appid."""
    url = f"https://api.steampowered.com/ISteamUserStats/GetGlobalAchievementPercentagesForApp/v2/?gameid={appid}"
    data = _safe_json(url)

    achievements = data.get("achievementpercentages", {}).get("achievements", [])
    df = pd.DataFrame(achievements)

    if not df.empty:
        df.rename(columns={"name": "achievement", "percent": "percent_unlocked"}, inplace=True)
        df["percent_unlocked"] = pd.to_numeric(df["percent_unlocked"], errors="coerce")
        df["appid"] = appid
        store_dataframe(df, "stats", if_exists="append")

    return df

# 4. Global: Store Metadata
def get_store_info(appid):
    """Return clean store info dict for a single appid."""
    url = f"https://store.steampowered.com/api/appdetails?appids={appid}&cc=us&l=en"
    data = _safe_json(url)

    block = data.get(str(appid), {})
    if not block.get("success"):
        return {}

    info = block.get("data", {}) or {}
    store_store_info(appid, info)
    return info

# 5. Global: Current Player Count
def get_current_players(appid):
    """Return integer player count or None."""
    url = f"https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid={appid}"
    data = _safe_json(url)

    player_count = data.get("response", {}).get("player_count", None)
    store_player_count(appid, player_count)
    return player_count

# 6. User: Profile Summary
def get_steam_user_info(steam_id, api_key):
    url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={api_key}&steamids={steam_id}"
    data = _safe_json(url)

    players = data.get("response", {}).get("players", [])
    if not players:
        return pd.DataFrame()

    p = players[0]
    df = pd.DataFrame([{
        "steamid": p.get("steamid"),
        "personaname": p.get("personaname"),
        "realname": p.get("realname"),
        "profileurl": p.get("profileurl"),
        "avatar": p.get("avatarfull"),
        "loccountrycode": p.get("loccountrycode"),
        "timecreated": pd.to_datetime(p.get("timecreated"), unit="s", errors="coerce"),
        "lastlogoff": pd.to_datetime(p.get("lastlogoff"), unit="s", errors="coerce")
    }])

    store_user_profile(df)
    return df

# 7. User: Owned Games
def get_owned_games(api_key, steam_id):
    url = f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?key={api_key}&steamid={steam_id}&include_appinfo=1&include_played_free_games=1"
    data = _safe_json(url)
    store_owned_games(steam_id, data)
    return data

# 8. User: Level
def get_steam_level(api_key, steam_id):
    url = f"https://api.steampowered.com/IPlayerService/GetSteamLevel/v1/?key={api_key}&steamid={steam_id}"
    return _safe_json(url)

# 9. User: Ban Info
def get_ban_info(api_key, steam_id):
    url = f"https://api.steampowered.com/ISteamUser/GetPlayerBans/v1/?key={api_key}&steamids={steam_id}"
    return _safe_json(url)

# 10. SteamSpy: Get ALL SteamSpy game stats
def get_steamspy_all():
    """Return a DataFrame of all SteamSpy game statistics."""
    url = "https://steamspy.com/api.php?request=all"
    data = _safe_json(url)

    df = pd.DataFrame.from_dict(data, orient="index")

    cols = ["appid", "name", "owners", "average_forever", "average_2weeks", "players_2weeks"]
    df = df[[c for c in cols if c in df.columns]]

    return df

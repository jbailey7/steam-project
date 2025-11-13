import requests
import pandas as pd


def get_top_games(limit=100):
    """Fetch the top N most played games with their appids."""
    charts_url = "https://api.steampowered.com/ISteamChartsService/GetMostPlayedGames/v1/"
    charts_data = requests.get(charts_url).json()
    top_games = charts_data["response"]["ranks"][:limit]

    games = {}
    for g in top_games:
        appid = g["appid"]
        info = requests.get(f"https://store.steampowered.com/api/appdetails?appids={appid}").json()
        if info.get(str(appid), {}).get("success"):
            name = info[str(appid)]["data"]["name"]
        else:
            name = f"App {appid}"
        games[name] = appid

    return games


def get_news(games):
    """Fetch recent news for each game."""
    all_news = []
    for name, appid in games.items():
        news_url = f"https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/?appid={appid}&count=10&format=json"
        res = requests.get(news_url)
        if res.status_code != 200:
            print(f"Failed to fetch news for {name}")
            continue

        news_items = res.json().get("appnews", {}).get("newsitems", [])
        for item in news_items:
            all_news.append({
                "game_name": name,
                "appid": appid,
                "title": item.get("title"),
                "author": item.get("author"),
                "feedlabel": item.get("feedlabel"),
                "date": item.get("date"),
                "url": item.get("url")
            })

    df = pd.DataFrame(all_news)
    df["date"] = pd.to_datetime(df["date"], unit="s", errors="coerce")
    return df


def get_stats(games):
    """Fetch global achievement percentages for each game."""
    all_stats = []
    for name, appid in games.items():
        stats_url = f"https://api.steampowered.com/ISteamUserStats/GetGlobalAchievementPercentagesForApp/v2/?gameid={appid}"
        res = requests.get(stats_url)
        if res.status_code != 200:
            print(f"Failed to fetch stats for {name}")
            continue

        achievements = res.json().get("achievementpercentages", {}).get("achievements", [])
        for a in achievements:
            all_stats.append({
                "game_name": name,
                "appid": appid,
                "achievement": a.get("name"),
                "percent_unlocked": a.get("percent")
            })

    return pd.DataFrame(all_stats)

import requests
import pandas as pd

# Existing imports like get_top_games(), get_news(), etc.

def get_steam_user_info(steam_id, api_key):
    """
    Fetch Steam user information for a given SteamID64.
    """
    url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={api_key}&steamids={steam_id}"
    res = requests.get(url)

    if res.status_code != 200:
        print(f"Failed to fetch user info for {steam_id}")
        return pd.DataFrame()

    players = res.json().get("response", {}).get("players", [])
    if not players:
        print(f"No player found for {steam_id}")
        return pd.DataFrame()

    data = players[0]
    df = pd.DataFrame([{
        "steamid": data.get("steamid"),
        "personaname": data.get("personaname"),
        "realname": data.get("realname"),
        "profileurl": data.get("profileurl"),
        "avatar": data.get("avatarfull"),
        "personastate": data.get("personastate"),
        "loccountrycode": data.get("loccountrycode"),
        "timecreated": pd.to_datetime(data.get("timecreated"), unit="s", errors="coerce"),
        "lastlogoff": pd.to_datetime(data.get("lastlogoff"), unit="s", errors="coerce")
    }])

    return df


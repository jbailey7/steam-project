from api import (
    get_top_games,
    get_news,
    get_stats,
    get_steamspy_all,
    get_store_info,
    get_current_players,
    get_steam_user_info,
    get_owned_games,
)
from database import store_dataframe, list_tables, store_steamspy_table

# Optional: configure user credentials for personal endpoints
STEAM_API_KEY = None  # set to your Steam Web API key as needed
STEAM_USER_ID = None  # set to the 64-bit SteamID you want to sync


def main():
    # Step 1: Get top 50 games
    games = get_top_games()

    # Step 2: Get news for each game
    news_df = get_news(games)

    # Step 3: Get stats for each game
    stats_df = get_stats(games)

    #n Step 4: Get steamspy table for each game
    df = get_steamspy_all()
    
    # Step 5: Store data in database
    store_dataframe(news_df, "news")
    store_dataframe(stats_df, "stats")
    store_steamspy_table(df)

    # Step 6: Persist store info & player counts for first N games
    for app_name, appid in list(games.items())[:50]:
        get_store_info(appid)
        get_current_players(appid)

    # Step 7: Optionally fetch user-specific information
    if STEAM_API_KEY and STEAM_USER_ID:
        get_steam_user_info(STEAM_USER_ID, STEAM_API_KEY)
        get_owned_games(STEAM_API_KEY, STEAM_USER_ID)
    else:
        print("Skipping user-specific endpoints; set STEAM_API_KEY and STEAM_USER_ID to enable.")

    print("Current tables:", list_tables())

if __name__ == "__main__":
    main()

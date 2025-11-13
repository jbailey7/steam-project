from api import get_top_games, get_news, get_stats
from database import store_dataframe, list_tables

def main():
    # Step 1: Get top 50 games
    games = get_top_games()

    # Step 2: Get news for each game
    news_df = get_news(games)

    # Step 3: Get stats for each game
    stats_df = get_stats(games)

    # Step 4: Store data in database
    store_dataframe(news_df, "news")
    store_dataframe(stats_df, "stats")

    print("Current tables:", list_tables())

if __name__ == "__main__":
    main()

import json
import os

import altair as alt
import pandas as pd
import streamlit as st

# Import API functions from the src package
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
from src.database import load_table

# CACHE LAYER — prefer DB, fall back to API
def cached_top_games(limit=25):
    df = load_table("games")
    if not df.empty and {"appid", "name"}.issubset(df.columns):
        if "players_2weeks" in df.columns:
            df = df.sort_values("players_2weeks", ascending=False)
        df = df.head(limit)
        games = dict(zip(df["name"], df["appid"]))
        if games:
            return games
    return get_top_games(limit)

def cached_news(appid):
    df = load_table("news")
    if not df.empty and "appid" in df.columns:
        df = df[df["appid"] == appid].copy()
        if not df.empty and "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
        if not df.empty:
            return df
    return get_news(appid)

def cached_stats(appid):
    df = load_table("stats")
    if not df.empty and "appid" in df.columns:
        df = df[df["appid"] == appid].copy()
        if not df.empty and "percent_unlocked" in df.columns:
            df["percent_unlocked"] = pd.to_numeric(df["percent_unlocked"], errors="coerce")
        if not df.empty:
            return df
    return get_stats(appid)

def cached_store(appid):
    df = load_table("store_metadata")
    if not df.empty and "appid" in df.columns:
        row = df[df["appid"] == appid]
        if not row.empty:
            row = row.iloc[0]
            if "raw_json" in row:
                try:
                    res = json.loads(row["raw_json"])
                    return res
                except Exception as e:
                    print(f"cached_store exception: {e}")
                    pass
            return row.to_dict()        
    return get_store_info(appid)

def cached_players(appid):
    df = load_table("player_counts")
    if not df.empty and "appid" in df.columns:
        sub = df[df["appid"] == appid].copy()
        if "retrieved_at" in sub.columns:
            sub["retrieved_at"] = pd.to_datetime(sub["retrieved_at"], errors="coerce")
            sub = sub.sort_values("retrieved_at")
        if not sub.empty and "player_count" in sub.columns:
            return int(sub.iloc[-1]["player_count"])
    return get_current_players(appid)

def cached_user(steam_id, key):
    df = load_table("user_profiles")
    if not df.empty and "steamid" in df.columns:
        sub = df[df["steamid"] == steam_id].copy()
        if not sub.empty:
            for col in ("timecreated", "lastlogoff"):
                if col in sub.columns:
                    sub[col] = pd.to_datetime(sub[col], errors="coerce")
            return sub
    return get_steam_user_info(steam_id, key)

def cached_owned(steam_id, key):
    df = load_table("owned_games")
    if not df.empty and "steamid" in df.columns:
        sub = df[df["steamid"] == steam_id].copy()
        if not sub.empty:
            games = sub.drop(columns=["steamid"], errors="ignore").to_dict(orient="records")
            return {"response": {"games": games, "game_count": len(games)}}
    return get_owned_games(key, steam_id)

def main():
    # Page Config + Dark Theme CSS
    st.set_page_config(
        page_title="Steam Analytics Dashboard",
        layout="centered",
    )

    api_key = os.getenv("STEAM_API_KEY")
    if not api_key:
        st.write("NO API KEY DETECTED")
        st.stop()

    # Dark Mode Styling
    st.markdown("""
    <style>
    body, .stApp {
        background-color: #111 !important;
    }
    html, body, [class*="css"] {
        color: #EEE !important;
        font-family: 'Inter', sans-serif;
    }
    h1, h2, h3 {
        color: #FFF !important;
        font-weight: 700 !important;
    }
    div[data-testid="metric-container"] {
        background: #1c1c1c;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0px 0px 10px #000;
        border: 1px solid #333;
    }
    [data-testid="stDataFrame"] {
        background-color: #1c1c1c !important;
    }
    .stTextInput > div > div > input {
        background-color: #222 !important;
        color: #EEE !important;
    }
    .stSelectbox > div > div {
        background-color: #222 !important;
        color: #EEE !important;
    }
    .stTabs [data-baseweb="tab"] {
        color: #DDD !important;
        background-color: #222 !important;
        border-radius: 10px;
        padding: 10px 15px;
        font-size: 18px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #333 !important;
        color: #FFF !important;
        font-weight: 700;
    }
    a {
        color: #8ab4f8 !important;
        text-decoration: none;
    }
    </style>
    """, unsafe_allow_html=True)


    # UI Title
    st.title("🎮 Steam Analytics Dashboard")

    st.image("images/steam-logo.jpg", use_container_width=True)

    # adding section for adding steam accounts
    if "accounts" not in st.session_state:
        st.session_state.accounts = []

    if "selected_account" not in st.session_state:
        st.session_state.selected_account = None

    st.subheader("👤 Saved Steam Accounts")

    # Add new account
    new_id = st.text_input("Add SteamID64", placeholder="7656119...")

    if st.button("➕ Add Account"):
        if not new_id:
            st.warning("Enter a valid SteamID64.")
        elif new_id in st.session_state.accounts:
            st.warning("SteamID already exists.")
        else:
            st.session_state.accounts.append(new_id)
            st.success(f"Added {new_id}")
            st.rerun()

    # Saved accounts list
    for acc in st.session_state.accounts:
        c1, c2, c3 = st.columns([3, 1, 1])
        c1.write(acc)

        # Delete
        if c2.button("❌", key=f"del-{acc}"):
            st.session_state.accounts.remove(acc)
            if st.session_state.selected_account == acc:
                st.session_state.selected_account = None
            st.rerun()

        # Load
        if c3.button("🔍", key=f"load-{acc}"):
            st.session_state.selected_account = acc
            st.session_state.page = "🔍 Steam User Lookup"
            st.rerun()

    st.markdown("---")
    
    # pages
    if "page" not in st.session_state:
        st.session_state.page = "🔍 Steam User Lookup"

    page = st.segmented_control(
        "Navigation",
        ["🔍 Steam User Lookup", "🌍 Global Game Explorer", "📊 Global Metrics"],
        key="page",
    )
    
    # Use the same api_key for user lookups
    if not api_key:
        st.error("No STEAM_API_KEY provided")
        st.stop()
        
    # page 1 — Steam User Lookup
    if page == "🔍 Steam User Lookup":

        st.header("🔍 Steam User Lookup")

        steam_id = st.session_state.selected_account

        if not steam_id:
            st.info("Select an account above to load profile data.")
            st.stop()
        
        user_df = cached_user(steam_id, api_key)

        if user_df.empty:
            st.error("No user found for this SteamID64.")
            st.stop()

        u = user_df.iloc[0]

        colA, colB = st.columns([1, 3])

        with colA:
            st.image(u["avatar"], width=200)

        with colB:
            st.subheader(u["personaname"])
            if pd.notna(u["realname"]):
                st.write(f"Real Name: **{u['realname']}**")

            st.write(f"Country: **{u['loccountrycode']}**")
            created = u["timecreated"]
            logoff = u["lastlogoff"]

            st.write(f"Account Created: **{created.date() if pd.notna(created) else 'N/A'}**")
            st.write(f"Last Logoff: **{logoff.date() if pd.notna(logoff) else 'N/A'}**")
            st.markdown(f"[Open Steam Profile]({u['profileurl']})")

        st.markdown("---")
        st.subheader("📈 User Stats")

        owned = cached_owned(steam_id, api_key)
        level = get_steam_level(api_key, steam_id)
        bans = get_ban_info(api_key, steam_id)

        game_count = owned.get("response", {}).get("game_count", 0)
        games_list = owned.get("response", {}).get("games", [])

        total_minutes = sum(g.get("playtime_forever", 0) for g in games_list)
        total_hours = round(total_minutes / 60, 1)

        player_level = level.get("response", {}).get("player_level", "N/A")
        ban_info = bans.get("players", [{}])[0]
        vac = ban_info.get("NumberOfVACBans", 0)
        gb = ban_info.get("NumberOfGameBans", 0)

        c1, c2, c3 = st.columns(3)
        c1.metric("Steam Level", player_level)
        c2.metric("Games Owned", game_count)
        c3.metric("Total Playtime (hrs)", total_hours)

        st.write(f"VAC Bans: **{vac}**")
        st.write(f"Game Bans: **{gb}**")

        st.subheader("🎮 Top 5 Most Played Games")
        sorted_games = sorted(games_list, key=lambda g: g.get("playtime_forever", 0), reverse=True)[:5]

        if not sorted_games:
            st.write("No game history.")
        else:
            for g in sorted_games:
                name = g.get("name", "Unknown")
                hours = round(g.get("playtime_forever", 0) / 60, 1)
                st.write(f"- **{name}** — {hours} hrs")

    # page 2 — Global Game Explorer
    elif page == "🌍 Global Game Explorer":

        st.header("🌍 Global Game Explorer")

        all_games  = cached_top_games(25)
        game_names = list(all_games.keys())

        selected = st.selectbox("Select a game:", game_names)

        if selected:
            appid = all_games[selected]

            st.subheader(f"📰 Latest News — {selected}")
            news_df = cached_news(appid)

            if news_df.empty:
                st.write("No news available.")
            else:
                temp = news_df[["date", "title", "feedlabel", "url"]].copy()
                temp = temp.rename(columns={
                    "date": "Date",
                    "title": "Headline",
                    "feedlabel": "Source",
                    "url": "Link"
                })

                # Format date
                temp["Date"] = temp["Date"].dt.strftime("%Y-%m-%d")

                st.data_editor(
                    temp,
                    hide_index=True,
                    use_container_width=True,
                    column_config={
                        "Link": st.column_config.LinkColumn(
                            label="Open Article",
                            help="Click to open news article",
                            display_text="Read"
                        )
                    }
                )

            st.subheader("🏆 Achievement Difficulty")
            stats_df = cached_stats(appid)

            if not stats_df.empty:
                chart = (
                    alt.Chart(stats_df)
                    .mark_bar(color="#4FA3FF")
                    .encode(
                        x=alt.X("percent_unlocked:Q", scale=alt.Scale(domain=[0, 100])),
                        y=alt.Y("achievement:N", sort="-x").axis(labelLimit=500),
                        tooltip=["achievement", "percent_unlocked"]
                    )
                )
                st.altair_chart(chart, use_container_width=True)

            st.subheader("🧊 Store Information")
            store = cached_store(appid)

            if store:
                col1, col2, col3 = st.columns(3)
                col1.metric("Price", store.get("price_overview", {}).get("final_formatted", "Free"))
                col2.metric("Metacritic", store.get("metacritic", {}).get("score", "N/A"))
                col3.metric("Release", store.get("release_date", {}).get("date", "N/A"))

                if store.get("genres"):
                    st.write("Genres: " + ", ".join(g["description"] for g in store["genres"]))

            st.subheader("👥 Current Player Count")
            players = cached_players(appid)
            if players is None:
                st.write("No data.")
            else:
                st.metric("Players Online", f"{players:,}")

    # page 3 — Global Metrics
    elif page == "📊 Global Metrics":
        st.header("📊 Global Steam Metrics")

        all_games = cached_top_games(25)

        # Top 10 most played
        st.subheader("🔥 Top 10 Most Played Games")

        player_count_rows = []
        player_price_rows = []
        price_types_rows = []
                
        # cached store loop
        for name, appid in all_games.items():
            store = cached_store(appid)
            if store:
                price = store.get("price_overview", {}).get("final", 0) / 100
                price_types_rows.append("Free" if store.get("is_free", False) else "Paid")
                
        # cached_players loop
        for name, appid in all_games.items():
            count = cached_players(appid)
            store = cached_store(appid)
            if count and store:
                price = store.get("price_overview", {}).get("final", 0) / 100
                player_price_rows.append({"Game": name, "Price": price, "Players": count})
                player_count_rows.append({"Game": name, "Players": count})

        df_players = pd.DataFrame(player_count_rows).sort_values("Players", ascending=False).head(10)

        chart = (
            alt.Chart(df_players)
            .mark_bar(color="#00CC88")
            .encode(
                x="Players:Q",
                y=alt.Y("Game:N", sort="-x"),
                tooltip=["Game", "Players"]
            )
        )
        st.altair_chart(chart, use_container_width=True)

        # Free vs Paid
        st.subheader("🪙 Free vs Paid Distribution")

        price_df = pd.DataFrame({"Type": price_types_rows})

        counts = price_df["Type"].value_counts().reset_index()
        counts.columns = ["Type", "Count"]

        # Pie chart
        pie = (
            alt.Chart(counts)
            .mark_arc(innerRadius=60)
            .encode(
                theta="Count:Q",
                color=alt.Color(
                    "Type:N",
                    scale=alt.Scale(range=["#4FA3FF", "#FF6A6A"])
                ),
                tooltip=["Type", "Count"]
            )
        )

        st.altair_chart(pie, use_container_width=True)

        st.subheader("🏷 Price vs Player Count Scatterplot")

        df_price_players = pd.DataFrame(player_price_rows)
        
        zoom = alt.selection_interval(bind='scales')

        scatter = (
            alt.Chart(df_price_players)
            .mark_circle(size=90)
            .encode(
                x=alt.X("Price:Q", title="Price ($)"),
                y=alt.Y("Players:Q", title="Players Online"),
                tooltip=["Game", "Price", "Players"]
            )
            .add_params(zoom)
        )

        st.altair_chart(scatter, use_container_width=True)

        # Genre frequency
        st.subheader("🎮🕹️👾 Top Genres")

        genre_counts = {}

        for name, appid in all_games.items():
            store = cached_store(appid)
            if store.get("genres"):
                for g in store["genres"]:
                    desc = g["description"]
                    genre_counts[desc] = genre_counts.get(desc, 0) + 1

        # ALL genres
        genre_all_df = pd.DataFrame({
            "Genre": list(genre_counts.keys()),
            "Count": list(genre_counts.values())
        }).sort_values("Count", ascending=False)

        # Multi-select ALL genres
        genre_filter = st.multiselect(
            "Filter by genre:",
            options=genre_all_df["Genre"].unique(),
            default=genre_all_df["Genre"].head(10).unique()
        )

        # Filter from the full dataset
        filtered = genre_all_df[genre_all_df["Genre"].isin(genre_filter)]

        highlight = alt.selection_point(on="mouseover", fields=["Genre"], empty="none")

        genre_chart = (
            alt.Chart(filtered)
            .mark_bar()
            .encode(
                x="Count:Q",
                y=alt.Y("Genre:N", sort="-x"),
                color=alt.value("#FF8C42"),
                opacity=alt.condition(
                    highlight,
                    alt.value(1.0),
                    alt.value(0.4)
                ),
                tooltip=["Genre", "Count"]
            )
            .add_params(highlight)
        )

        st.altair_chart(genre_chart, use_container_width=True)

        st.subheader("🎯 Average Metacritic Score by Genre")

        rows = []
        for name, appid in all_games.items():
            store = cached_store(appid)
            if not store:
                continue
            score = store.get("metacritic", {}).get("score")
            genres = store.get("genres", [])
            for g in genres:
                rows.append({"Genre": g["description"], "Score": score})

        df = pd.DataFrame(rows).dropna()

        chart = (
            alt.Chart(df)
            .mark_bar()
            .encode(
                x="Genre:N",
                y=alt.Y(
                    "mean(Score):Q",
                    axis=alt.Axis(title="Average Score")
                ),
                tooltip=[
                    "Genre:N",
                    alt.Tooltip(
                        "mean(Score):Q",
                        title="Average Score",
                        format=".2f"
                    )
                ]
            )
        )
        st.altair_chart(chart, use_container_width=True)

if __name__ == "__main__":
    main()

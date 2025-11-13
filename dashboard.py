import streamlit as st
import pandas as pd
from api import get_steam_user_info
import os

API_KEY = os.getenv("STEAM_API_KEY")

def main():
    st.title("Steam User Dashboard")

    st.write("Enter a SteamID64 to view profile details.")
    steam_id = st.text_input("SteamID64", placeholder="e.g. 76561197960435530")

    if st.button("Fetch User Info"):
        if not steam_id:
            st.warning("Please enter a valid SteamID64.")
        else:
            with st.spinner("Fetching user info..."):
                df = get_steam_user_info(steam_id, API_KEY)

            if df.empty:
                st.error("No user found. Check the SteamID or API key.")
            else:
                data = df.iloc[0]

                st.image(data["avatar"], width=128)
                st.subheader(data["personaname"])
                if pd.notna(data["realname"]):
                    st.write(f"**Real name:** {data['realname']}")
                st.write(f"**Country:** {data['loccountrycode']}")
                st.write(f"**Account Created:** {data['timecreated'].date() if pd.notna(data['timecreated']) else 'N/A'}")
                st.write(f"**Last Logoff:** {data['lastlogoff'].date() if pd.notna(data['lastlogoff']) else 'N/A'}")

                st.markdown(f"[Open Steam Profile]({data['profileurl']})")

if __name__ == "__main__":
    main()

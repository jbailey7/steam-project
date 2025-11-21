# steam-project
A fully interactive Streamlit dashboard that visualizes Steam user data, global game metrics, achievement difficulty, live player counts, store metadata, and more. The app combines Steam Web API calls with a SQLite database to deliver fast, cached, and dynamic insights.

### Docker Usage
1. Set `DB_PATH` to your desired database path. If not value is provided then "steam.db" will be used as default.
2. Set `AIRFLOW_FERNET_KEY` as an environment variable. This value can be anything, but it will be used to encrypt data. 
3. Set `STEAM_API_KEY` as an environment variable. Can obtain a key here: https://steamcommunity.com/dev
4. Run `docker compose up --build`
5. Navigate to `http://localhost:8501/` to view the dashboard!

### Airflow
To view the Airflow UI, follow steps 1-4 from the Usage section above. Then: 
1. In a separate tab, run `docker exec -it airflow-api-server bash`
2. Inside the container, run: 

airflow users create \
  --username admin \
  --firstname <firstname> \
  --lastname <lastname> \
  --role Admin \
  --email <email> \
  --password <password>

An example of the following is: 
airflow users create \
  --username admin \
  --firstname Jack \
  --lastname Bailey \
  --role Admin \
  --email jack@example.com \
  --password password

3. Navigate to `http://localhost:8080/` and use the credentials you created to sign in. 


### Streamlit Usage
1. Set `DB_PATH` to your desired database path. If not value is provided then "steam.db" will be used as default. To run locally with streamlit: 
2. Set `STEAM_API_KEY` as an environment variable. Can obtain a key here: https://steamcommunity.com/dev
3. Run `PYTHONPATH=. streamlit run src/dashboard.py`


### How to Use This Dashboard
1. Enter your SteamID64 into the input box at the top of the page. This is the unique 17-digit identifier for your Steam account.
2. Click “Add Account” to save it. Your saved Steam accounts will appear directly underneath.
3. Use the red X button to delete a saved account, or the magnifying glass button to load the selected account’s data.


### Don’t Know Your SteamID64?
If you’re not sure what your SteamID64 is, you can easily find it here: 
https://steamid.io/lookup/
Just paste your Steam profile URL into the search bar, and it will show your SteamID64.


### Tabs
**1. Steam User Lookup:** Look up any SteamID64 and view their stats
**2. Global Game Explorer:** Explore the top 25 most-played games on Steam
**3. Global Steam Metrics:** Analyze global trends across the top games

# Enjoy!!!

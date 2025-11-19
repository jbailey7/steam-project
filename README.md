# steam-project

### Usage
1. Set `DB_PATH` to your desired database path. If not value is provided then "steam.db" will be used as default.
2. Set `AIRFLOW_FERNET_KEY` as an environment variable. This value can be anything, but will be used to encrypt data. 
3. Set `STEAM_API_KEY` as an environment variable. Can obtain a key here: https://steamcommunity.com/dev
4. Create an .env file. The file should have the following structure: 

AIRFLOW_ADMIN_USERNAME=<username-value>
AIRFLOW_ADMIN_ROLE=admin=<role-value>

(can use "admin" for both values)

5. Run `docker compose up --build`
6. Navigate to `http://localhost:8501/` to view the dashboard!

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

To run locally with streamlit: 
`PYTHONPATH=. streamlit run src/dashboard.py`

# steam-project

### Usage
1. Set `DB_PATH` to your desired database path. If not value is provided then "steam.db" will be used as default.
2. Set `AIRFLOW_FERNET_KEY` as an environment key. This value can be anything, but will be used to encrypt data. 
2. Run `airflow db migrate`
3. Run `docker compose build`
4. Run `docker compose up`

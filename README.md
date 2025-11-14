# steam-project

### Usage
1. Set `DB_PATH` to your desired database path. If not value is provided then "steam.db" will be used as default.
2. Set `AIRFLOW_FERNET_KEY` as an environment key. This value can be anything, but will be used to encrypt data. s
3. Create an .env file. The file should have the following structure: 

AIRFLOW_ADMIN_USERNAME=<username-value>
AIRFLOW_ADMIN_ROLE=admin=<role-value>

(can use "admin" for both values)

4. Run `docker compose up --build`
5. Navigate to `http://localhost:8501/` to view the dashboard!

### Airflow
To view the Airflow UI, follow steps 1-4 from the Usage section above. Then: 
1. In a separate tab, run `docker exec -it airflow-api-server bash`
2. Then `cat simple_auth_manager_passwords.json.generated` will show the generated airflow password
3. Navitage to `http://localhost:8080/`
4. Sign in with username: "admin" and password: <the value from above>
5. View the UI!

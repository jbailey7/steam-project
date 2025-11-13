import sys
from datetime import datetime, timedelta

from airflow.sdk import DAG
from airflow.providers.standard.operators.python import PythonOperator

PROJECT_DIR = "/opt/airflow/steam_project"

if PROJECT_DIR not in sys.path:
    sys.path.append(PROJECT_DIR)

from main import main as run_steam_etl

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


with DAG(
    dag_id="steam_etl",
    default_args=default_args,
    description="Fetch Steam top games/news/stats and load into SQLite",
    schedule_interval="@daily",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["steam"],
) as dag:

    run_etl_task = PythonOperator(
        task_id="run_steam_etl",
        python_callable=run_steam_etl,
    )

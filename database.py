import sqlite3
import pandas as pd
import os

DB_PATH = "steam.db"

def create_connection():
    """Create a SQLite database connection."""
    conn = sqlite3.connect(DB_PATH)
    return conn

def store_dataframe(df, table_name):
    """Store a pandas DataFrame in the database."""
    if df.empty:
        print(f"No data to store for {table_name}")
        return
    conn = create_connection()
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.close()
    print(f"Stored {len(df)} records in '{table_name}' table.")

def load_table(table_name):
    """Load a table back into a DataFrame."""
    conn = create_connection()
    df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    conn.close()
    return df

def list_tables():
    """Show available tables in the database."""
    conn = create_connection()
    tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table';", conn)
    conn.close()
    return tables["name"].tolist()

def store_steamspy_table(df):
    """Store SteamSpy data into steam.db as table 'games'."""
    store_dataframe(df, "games")
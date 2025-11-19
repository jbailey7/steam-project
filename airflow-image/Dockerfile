FROM apache/airflow:3.1.2

# Switch to airflow user (default user in this image)
USER airflow

# Install Python packages in the airflow user's environment
RUN pip install --no-cache-dir \
    pandas \
    requests \
    apache-airflow-providers-fab

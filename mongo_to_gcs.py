from airflow import DAG
from airflow.contrib.operators.mysql_to_gcs import MySqlToGoogleCloudStorageOperator
from airflow.operators.bash_operator import BashOperator
from datetime import datetime, timedelta
import airflow
from mongo_to_gcs.operators.mongo_operator import MongoToGcs
default_args = {
    'owner': 'mikeghen',
    'start_date':airflow.utils.dates.days_ago(1),
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG('mysql_to_gcs', default_args=default_args)



export_mongo = MongoToGcs(
    task_id='mongo_extract',
    mongo_conn_id='mongo_default',
    mongo_collection='things',
    mongo_database='admin',
    delegate_to = None,
    mongo_query={"id" : 1,"ip_address" : "251.71.120.203"},
    gcs_conn_id='google_cloud_storage_default',
    bucket='django_test2',
    filename='test/temp/data.json',
    dag=dag)

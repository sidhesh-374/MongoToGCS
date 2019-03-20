from airflow.plugins_manager import AirflowPlugin
from mongo_to_gcs.operators.mongo_operator import MongoToGcs



class MongodbToGCSPlugin(AirflowPlugin):
    name = "MongodbToGCSPlugin"
    operators = [MongoToGcs]
    # Leave in for explicitness
    hooks = []
    executors = []
    macros = []
    admin_views = []
    flask_blueprints = []
    menu_links = []

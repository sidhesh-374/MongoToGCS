import sys
from bson import json_util
import json
from airflow.contrib.hooks.mongo_hook import MongoHook
from airflow.contrib.hooks.gcs_hook import GoogleCloudStorageHook
from tempfile import NamedTemporaryFile
from airflow.models import BaseOperator
from airflow.plugins_manager import AirflowPlugin



PY3 = sys.version_info[0] == 3


class MongoToGcs(BaseOperator):
    """
    Mongo -> GCS
    :param mongo_conn_id:           The source mongo connection id.
    :type mongo_conn_id:            string
    :param mongo_collection:        The source mongo collection.
    :type mongo_collection:         string
    :param mongo_database:          The source mongo database.
    :type mongo_database:           string
    :param mongo_query:             The specified mongo query.
    :type mongo_query:              string
    :param gcs_conn_id:             The destination gcs connnection id.
    :type gcs_conn_id:              string
    :param bucket:                  The destination gcs bucket.
    :type gcs_bucket:               string
    :param filename:                The destination s3 key.
    :type gcs_dest_filename:        string
    """

    # TODO This currently sets job = queued and locks job
    #template_fields = ['s3_key', 'mongo_query']

    def __init__(self,
                 mongo_conn_id,
                 mongo_collection,
                 mongo_database,
                 mongo_query,
                 bucket,
                 filename,
                 delegate_to,
                 gcs_conn_id='google_cloud_default',
                 *args, **kwargs):
        super(MongoToGcs, self).__init__(*args, **kwargs)
        # Conn Ids
        self.mongo_conn_id = mongo_conn_id
        # Mongo Query Settings
        self.mongo_db = mongo_database
        self.mongo_collection = mongo_collection
        # Grab query and determine if we need to run an aggregate pipeline
        self.mongo_query = mongo_query
        self.is_pipeline = True if isinstance(self.mongo_query, list) else False
        #GCS Settings
        self.bucket = bucket
        self.filename = filename
        self.google_cloud_storage_conn_id = gcs_conn_id
        self.delegate_to = delegate_to
        # KWARGS
        self.replace = kwargs.pop('replace', False)

    def execute(self, context):
        """
        Executed by task_instance at runtime
        """

        file_to_upload = self._get_mongo_doc()
        for file_handle in file_to_upload.values():
            file_handle.flush()

        self._upload_to_gcs(file_to_upload)

        for file_handle in file_to_upload.values():
            file_handle.close()

    def _stringify(self, iter, joinable='\n'):
        """
        Takes an interable (pymongo Cursor or Array) containing dictionaries and
        returns a stringified version using python join
        """
        return joinable.join([json_util.dumps(doc) for doc in iter])

    def transform(self, docs):
        """
        Processes pyMongo cursor and returns single array with each element being
                a JSON serializable dictionary
        MongoToS3Operator.transform() assumes no processing is needed
        ie. docs is a pyMongo cursor of documents and cursor just needs to be
            converted into an array.
        """
        return [doc for doc in docs]
    def _get_mongo_doc(self):
        """
        It gets the document from mongodb server connection. convert it into appropriate,
        string into json file
        :param self:
        :return:
        """

        mongo_conn = MongoHook(self.mongo_conn_id).get_conn()
        collection = mongo_conn.get_database(self.mongo_db).get_collection(self.mongo_collection)
        results = collection.aggregate(self.mongo_query) if self.is_pipeline else collection.find(self.mongo_query)
        docs_str = self._stringify(self.transform(results))
        print(docs_str)
        #file_no = 0
        tmp_file_handle = NamedTemporaryFile(delete=True)
        #tmp_file_handles = {self.filename:tmp_file_handle}
        if PY3:
           docs_str = docs_str.replace("$",'').encode('utf-8')
        tmp_file_handle.write(docs_str)
        tmp_file_handles = {self.filename:tmp_file_handle}
        final_json_file = tmp_file_handles
        return final_json_file

    def _upload_to_gcs(self, files_to_upload):
        """
        Upload all of the file splits (and optionally the schema .json file) to
        Google cloud storage.
        """
        hook = GoogleCloudStorageHook(
            google_cloud_storage_conn_id=self.google_cloud_storage_conn_id,
            delegate_to=self.delegate_to)
        for object, tmp_file_handle in files_to_upload.items():
            hook.upload(self.bucket, object, tmp_file_handle.name, 'application/json')

class mongo_to_gcs(AirflowPlugin):
    name = 'mongo_to_gcs'
    operators = [MongoToGcs]

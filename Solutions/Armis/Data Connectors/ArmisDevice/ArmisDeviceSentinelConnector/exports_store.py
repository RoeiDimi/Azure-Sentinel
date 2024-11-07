import logging

from enum import Enum
from azure.data.tables import TableClient, UpdateMode
from azure.core.exceptions import ResourceNotFoundError, ResourceExistsError, HttpResponseError


class ExportsTableStore:

    def __init__(self, connection_string, table_name):
        self.connection_string = connection_string
        self.table_name = table_name

    def create(self):
        with TableClient.from_connection_string(self.connection_string, self.table_name) as table_client:
            try:
                table_client.create_table()
                logging.info("Checkpoint Table created")
            except ResourceExistsError:
                logging.warning("Table already exists")

    def post(self, pk: str, rk: str, data: dict = None):
        with TableClient.from_connection_string(self.connection_string, self.table_name) as table_client:
            entity_template = {
                "PartitionKey": pk,
                "RowKey": rk,
            }
            if data is not None:
                entity_template.update(data)
            try:
                table_client.create_entity(entity_template)
            except Exception as e:
                logging.warning("could not post entity to table")
                logging.warning(e)
                raise e

    def get(self, pk: str, rk: str):
        with TableClient.from_connection_string(self.connection_string, self.table_name) as table_client:
            try:
                logging.info(
                    "looking for {} - {} on table {}".format(pk, rk, self.table_name))
                return table_client.get_entity(pk, rk)
            except ResourceNotFoundError:
                return None

    def upsert(self, pk: str, rk: str, data: dict = None):
        with TableClient.from_connection_string(self.connection_string, self.table_name) as table_client:
            logging.info("upserting {} - {} on table {}".format(pk, rk, self.table_name))
            entity_template = {
                "PartitionKey": pk,
                "RowKey": rk,
            }
            if data is not None:
                entity_template.update(data)
            return table_client.upsert_entity(mode=UpdateMode.REPLACE, entity=entity_template)

    def update_if_found(self, pk: str, rk: str, data: dict = None):
        if self.get(pk, rk) is not None:
            self.merge(pk, rk, data)

    def query_by_partition_key(self, pk):
        table_client = TableClient.from_connection_string(
            self.connection_string, self.table_name)
        parameters = {u"key": pk}
        name_filter = u"PartitionKey eq @key"
        try:
            return table_client.query_entities(name_filter, parameters=parameters)
        except HttpResponseError as e:
            print(e.message)
            return []

    def batch(self, operations):
        with TableClient.from_connection_string(self.connection_string, self.table_name) as table_client:
            return table_client.submit_transaction(operations=operations)

    def list_all(self):
        table_client = TableClient.from_connection_string(
            self.connection_string, self.table_name)
        return table_client.list_entities()

    def merge(self, pk: str, rk: str, data: dict = None):
        with TableClient.from_connection_string(self.connection_string, self.table_name) as table_client:
            logging.info("upserting {} - {} on table {}".format(pk, rk, self.table_name))
            entity_template = {
                "PartitionKey": pk,
                "RowKey": rk,
            }
            if data is not None:
                entity_template.update(data)
            return table_client.upsert_entity(mode=UpdateMode.MERGE, entity=entity_template)



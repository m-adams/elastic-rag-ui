### WARNING This is not reccomended for production use ###

from elasticsearch import Elasticsearch
import logging
from logging import StreamHandler

# This is a custom logging handler that will send logs directly to elasticsearch
class ElasticHandler(StreamHandler):
    def __init__(self, level,es_client: Elasticsearch, index: str):
        StreamHandler.__init__(self)
        self._es_client = es_client
        self._index = index
    def emit(self, record):
      msg = self.format(record)
      #print(msg)
      #print(self._index)
      #print(self._es_client)
      result=self._es_client.index(index=self._index, document=msg)
      #print(result)
      if result.get("result") != "created":
        print("Error sending log to elasticsearch")
        print(result)

# This is a custom logging filter that will add the event.dataset field to the log record as it's madatory
class SystemLogFilter(logging.Filter):
    def __init__(self, EVENT_DATASET_LOGS):
        logging.Filter.__init__(self)
        self.EVENT_DATASET_LOGS = EVENT_DATASET_LOGS
    def filter(self, record):
        if not hasattr(record, 'extra'):
            record.extra= {"event.dataset": self.EVENT_DATASET_LOGS}
        else:
          if not hasattr(record.extra,'event.dataset'):
            record.extra["event.dataset"]= self.EVENT_DATASET_LOGS
        return True
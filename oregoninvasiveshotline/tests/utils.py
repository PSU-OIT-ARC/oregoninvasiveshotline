import logging

from elasticsearch import Elasticsearch

from django.conf import settings

logger = logging.getLogger(__name__)


def refresh_search_indexes():
    for name, connection in list(settings.HAYSTACK_CONNECTIONS.items()):
        try:
            es = Elasticsearch(connection['URL'])
            es.indices.refresh(index=connection['INDEX_NAME'])
        except Exception as exc:
            logger.error("Error in 'refresh_search_indexes': {0!s}".format(exc))


def clear_search_indexes():
    for name, connection in list(settings.HAYSTACK_CONNECTIONS.items()):
        try:
            es = Elasticsearch(connection['URL'])
            es.indices.delete(index=connection['INDEX_NAME'])
            es.indices.create(index=connection['INDEX_NAME'])
        except Exception as exc:
            logger.error("Error in 'clear_search_indexes': {0!s}".format(exc))

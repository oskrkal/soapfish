import os
import six
from lxml import etree
from . import utils
from . import xsdspec


class XSDSchemaResolver(object):
    def __init__(self, base_path=None, locations=None):
        """
        :param base_path: base path on the file system relatively to which all schema locations will be resolved
        """
        self.base_path = os.path.abspath(base_path or six.moves.getcwd())
        self.locations = locations if locations else {}
        self._schema_cache = {}

    def __call__(self, schema_location=None, namespace=None, base_path=None):
        return self.resolve_schema(schema_location, namespace, base_path=base_path)

    def resolve_schema(self, schema_location=None, namespace=None, base_path=None):
        if not schema_location and namespace:
            schema_location = self.locations.get(namespace)

        if not schema_location:
            return None

        schema_path, _ = self._resolve_path(schema_location, base_path)

        schema = self._find_cached_schema(schema_path)
        if not schema:
            schema = self._load_schema(schema_path)
            self._cache_schema(schema_path, schema)

        return schema

    def expire_cache(self, schema_location=None, base_path=None):
        if schema_location:
            schema_path, _ = self._resolve_path(schema_location, base_path=base_path)
            self._schema_cache.pop(schema_path, None)
        else:
            self._schema_cache.clear()

    def _find_cached_schema(self, path):
        return self._schema_cache.get(path)

    def _load_schema(self, path):
        schema_xsd = utils.open_document(path)
        schema_xsd = etree.fromstring(schema_xsd)
        return xsdspec.Schema.parse_xmlelement(schema_xsd)

    def _cache_schema(self, path, schema):
        if schema:
            self._schema_cache[path] = schema

    def _resolve_path(self, schema_location, base_path):
        path, cwd, _ = utils.resolve_location(schema_location, base_path or self.base_path)
        if not "://" in path:
            path = os.path.abspath(path)
        if cwd:
            cwd = os.path.abspath(cwd)
        return path, cwd

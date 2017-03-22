import os
import six
from six.moves import urllib
from lxml import etree
from . import utils
from . import xsdspec


def resolve_location(schema_location, base_path=None):
    if not schema_location:
        raise ValueError("The location argument must be a non-empty string.")
    if not base_path:
        base_path = six.moves.getcwd()

    # resolve path in context of base path
    if "://" not in schema_location and "://" not in base_path:
        resolved_path = os.path.abspath(os.path.join(os.path.normpath(base_path), os.path.normpath(schema_location)))
    else:
        resolved_path = urllib.parse.urljoin(base_path, schema_location)

    return resolved_path


def get_parent_directory(schema_location):
    if not schema_location:
        return None
    if "://" not in schema_location:
        return os.path.dirname(schema_location)

    split_url = urllib.parse.urlsplit(schema_location)
    url_path = split_url.path
    if url_path:
        url_path = split_url.path.rsplit("/", 1)
        url_path = (url_path[-2] + "/") if len(url_path) > 1 else "/"
    split_url = (split_url.scheme, split_url.netloc, url_path, None, None)
    return urllib.parse.urlunsplit(split_url)


class ResolvedSchema(object):
    def __init__(self, schema, location, base_path):
        self.schema = schema
        self.location = location
        self.base_path = base_path


class XSDSchemaResolver(object):
    def __init__(self, base_path=None):
        """
        :param base_path: base path on the file system relatively to which all schema locations will be resolved
        """
        self.base_path = base_path

    def resolve_schema(self, location, base_path=None):
        if not location:
            raise ValueError("The location parameter must be a non-empty string.")

        location = resolve_location(location, base_path=base_path or self.base_path)

        schema_xsd = utils.open_document(location)
        schema_xsd = etree.fromstring(schema_xsd)
        schema = xsdspec.Schema.parse_xmlelement(schema_xsd)

        return ResolvedSchema(schema, location, get_parent_directory(location))


class XSDCachedSchemaResolver(object):
    def __init__(self, resolver, locations=None):
        assert hasattr(resolver, "resolve_schema")
        self.resolver = resolver
        self.locations = locations if locations else {}
        self._schema_cache = {}

    def __call__(self, schema_location=None, namespace=None, base_path=None):
        return self.resolve_schema(schema_location=schema_location, namespace=namespace, base_path=base_path)

    @classmethod
    def create(cls, base_path=None, locations=None):
        return cls(XSDSchemaResolver(base_path), locations)

    def expire_cache(self, schema_location=None, base_path=None):
        if schema_location:
            cache_key = self.__get_cache_key(schema_location, base_path)
            self._schema_cache.pop(cache_key, None)
        else:
            self._schema_cache.clear()

    def resolve_schema(self, schema_location=None, namespace=None, base_path=None):
        if not schema_location and namespace:
            schema_location = self.locations.get(namespace)
        if not schema_location:
            return None

        cache_key = self.__get_cache_key(schema_location, base_path)
        resolved_schema = self._schema_cache.get(cache_key)

        if not resolved_schema:
            resolved_schema = self.resolver.resolve_schema(schema_location, base_path=base_path)
            if resolved_schema:
                self._schema_cache[cache_key] = resolved_schema

        return resolved_schema

    def __get_cache_key(self, schema_location, base_path):
        return resolve_location(schema_location, base_path=base_path or self.resolver.base_path)

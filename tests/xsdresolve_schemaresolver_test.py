import mock
import os
import six
from pythonic_testcase import (
    PythonicTestCase,
    assert_equals,
    assert_none,
    assert_true
)
from soapfish import xsdresolve


# Helper functions ------

def assert_all_equal(iterable, message=None):
    if not iterable:
        return
    expected = iterable[0]
    for i, item in enumerate(iterable[1:]):
        if item != expected:
            default_message = "%s != %s ([0] != [%d])" % (expected, item, i+1)
            if message is None:
                raise AssertionError(default_message + "; actual items: " + str(iterable))
            raise AssertionError(default_message + ": " + message)


# Tests -----------------

class ResolveLocationTest(PythonicTestCase):
    BASE_PATH = "basepath/"
    RELATIVE_PATH = "schema/location.xsd"
    ABSOLUTE_PATH = os.path.abspath(os.path.join(os.path.normpath(BASE_PATH), os.path.normpath(RELATIVE_PATH)))

    BASE_URL = "http://site/base/nested/"  # must end with / to work as expected
    ABSOLUTE_URL_PATH = "/absolute/location.xsd"
    RELATIVE_URL_PATH = "../some/location.xsd"
    ABSOLUTE_URL = "http://site/base/some/location.xsd"

    def test_resolve_none_raises_error(self):
        self.assertRaises(ValueError, xsdresolve.resolve_location, None)

    def test_resolve_abs_path(self):
        assert_equals(self.ABSOLUTE_PATH, xsdresolve.resolve_location(self.ABSOLUTE_PATH))

    def test_resolve_abs_url(self):
        assert_equals(self.ABSOLUTE_URL, xsdresolve.resolve_location(self.ABSOLUTE_URL))

    def test_resolve_relative_path_without_base_path(self):
        expected = os.path.normpath(os.path.join(six.moves.getcwd(), self.RELATIVE_PATH))
        assert_equals(expected, xsdresolve.resolve_location(self.RELATIVE_PATH))

    def test_resolve_relative_path(self):
        assert_equals(self.ABSOLUTE_PATH, xsdresolve.resolve_location(self.RELATIVE_PATH, base_path=self.BASE_PATH))

    def test_resolve_relative_url_path(self):
        assert_equals(self.ABSOLUTE_URL, xsdresolve.resolve_location(self.RELATIVE_URL_PATH, base_path=self.BASE_URL))

    def test_resolve_absolute_url_path(self):
        expected = "http://site/absolute/location.xsd"
        assert_equals(expected, xsdresolve.resolve_location(self.ABSOLUTE_URL_PATH, base_path=self.BASE_URL))

    def test_equivalent_paths_with_parent_dir_reference_resolve_to_same_location(self):
        paths = [
            xsdresolve.resolve_location("../dirB/file", base_path="basepath/dirA/"),
            xsdresolve.resolve_location("dirC/../dirB/file", base_path="basepath/"),
            xsdresolve.resolve_location("dirB/file", base_path="basepath/")
        ]
        assert_all_equal(paths)

    def test_equivalent_paths_with_current_dir_reference_resolve_to_same_location(self):
        paths = [
            xsdresolve.resolve_location("./dirA/././file", base_path="basepath/"),
            xsdresolve.resolve_location("dirA/file", base_path="basepath/./."),
            xsdresolve.resolve_location("dirA/file", base_path="basepath/")
        ]
        assert_all_equal(paths)

    def test_equivalent_relative_and_absolute_path_resolve_to_same_location(self):
        paths = [
            xsdresolve.resolve_location("dirA/file", base_path="basepath/"),
            xsdresolve.resolve_location(os.path.abspath("basepath/dirA/file"), base_path=os.path.abspath("anotherbase/")),
            xsdresolve.resolve_location("dirA/file", base_path=os.path.abspath("basepath/"))
        ]
        assert_all_equal(paths)

    def test_equivalent_urls_resolve_to_same_location(self):
        urls = [
            xsdresolve.resolve_location("dirC/../dirB/file", base_path="http://server/dirA/"),
            xsdresolve.resolve_location("../dirA/dirB/file", base_path="http://server/dirD/"),
            xsdresolve.resolve_location("dirA/dirB/././file", base_path="http://server/"),
            xsdresolve.resolve_location("http://server/dirA/dirB/file", base_path="http://whatever/")
        ]
        assert_all_equal(urls)


class LocationParentDirectoryTest(PythonicTestCase):
    def test_get_parent_of_none_returns_none(self):
        assert_none(xsdresolve.get_parent_directory(None))

    @mock.patch("soapfish.xsdresolve.os.path.dirname", autospec=True)
    def test_get_parent_of_abs_path_calls_dirname(self, dirname_mock):
        path = os.path.abspath("some/path")
        parent_path = "parent/path"
        dirname_mock.return_value = parent_path
        assert_equals(parent_path, xsdresolve.get_parent_directory(path))

    @mock.patch("soapfish.xsdresolve.os.path.dirname", autospec=True)
    def test_get_parent_of_relative_path_calls_dirname(self, dirname_mock):
        path = "some/path"
        parent_path = "parent/path"
        dirname_mock.return_value = parent_path
        assert_equals(parent_path, xsdresolve.get_parent_directory(path))

    def test_get_parent_of_file_url(self):
        assert_equals("http://site/some/", xsdresolve.get_parent_directory("http://site/some/schema"))

    def test_get_parent_of_file_url_with_query_string(self):
        assert_equals("http://site/some/", xsdresolve.get_parent_directory("http://site/some/schema?p1=a&p2=b/c"))

    def test_get_parent_of_dir_url(self):
        assert_equals("http://site/some/path/", xsdresolve.get_parent_directory("http://site/some/path/"))

    def test_get_parent_of_dir_url_with_query_string(self):
        assert_equals("http://site/some/path/", xsdresolve.get_parent_directory("http://site/some/path/?p1=a&p2=b/c"))

    def test_get_parent_of_root_url(self):
        assert_equals("http://site/", xsdresolve.get_parent_directory("http://site/"))

    def test_get_parent_of_root_url_with_query_string(self):
        assert_equals("http://site/", xsdresolve.get_parent_directory("http://site/?p1=a&p2=b/c"))


class XSDSchemaResolverTest(PythonicTestCase):
    SCHEMA = '<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" targetNamespace="http://schema/resolver/test" />'
    SCHEMA_NAMESPACE = "http://schema/resolver/test"
    SCHEMA_LOCATION = "schema/location.xsd"
    SCHEMA_BASE_PATH = "http://site/"
    SCHEMA_PARENT = "http://site/schema/"
    SCHEMA_URL = "http://site/schema/location.xsd"

    def setUp(self):
        self.resolve_location_patcher = mock.patch("soapfish.xsdresolve.resolve_location", autospec=True)
        self.resolve_location_mock = self.resolve_location_patcher.start()
        self.resolve_location_mock.return_value = self.SCHEMA_URL

        self.open_patcher = mock.patch("soapfish.xsdresolve.utils.open_document", autospec=True)
        self.open_mock = self.open_patcher.start()
        self.open_mock.return_value = self.SCHEMA

    def tearDown(self):
        self.open_patcher.stop()
        self.resolve_location_patcher.stop()

    def test_resolve_schema(self):
        resolver = xsdresolve.XSDSchemaResolver()
        resolved_schema = resolver.resolve_schema(self.SCHEMA_LOCATION)

        self.resolve_location_mock.assert_called_once_with(self.SCHEMA_LOCATION, base_path=None)
        self.open_mock.assert_called_once_with(self.SCHEMA_URL)
        self.verify_resolved_schema(resolved_schema)

    def test_resolve_schema_passes_base_path_from_init(self):
        resolver = xsdresolve.XSDSchemaResolver(base_path=self.SCHEMA_BASE_PATH)
        resolved_schema = resolver.resolve_schema(self.SCHEMA_LOCATION)

        self.resolve_location_mock.assert_called_once_with(self.SCHEMA_LOCATION, base_path=self.SCHEMA_BASE_PATH)
        self.open_mock.assert_called_once_with(self.SCHEMA_URL)
        self.verify_resolved_schema(resolved_schema)

    def test_resolve_schema_passes_base_path_from_method(self):
        resolver = xsdresolve.XSDSchemaResolver(base_path="some/base/path")
        resolved_schema = resolver.resolve_schema(self.SCHEMA_LOCATION, base_path=self.SCHEMA_BASE_PATH)

        self.resolve_location_mock.assert_called_once_with(self.SCHEMA_LOCATION, base_path=self.SCHEMA_BASE_PATH)
        self.open_mock.assert_called_once_with(self.SCHEMA_URL)
        self.verify_resolved_schema(resolved_schema)

    def test_resolve_schema_without_path_raises_error(self):
        resolver = xsdresolve.XSDSchemaResolver()
        self.assertRaises(ValueError, resolver.resolve_schema, None)

    def verify_resolved_schema(self, resolved_schema, namespace=SCHEMA_NAMESPACE, location=SCHEMA_URL, base_path=SCHEMA_PARENT):
        assert_equals(namespace, resolved_schema.schema.targetNamespace)
        assert_equals(location, resolved_schema.location)
        assert_equals(base_path, resolved_schema.base_path)


class XSDSchemaCachedResolverTest(PythonicTestCase):
    SCHEMA_NAMESPACE = "http://schema/resolver/test"
    SCHEMA_URL1 = "http://site/schema/location1.xsd"
    SCHEMA_URL2 = "http://site/schema/location2.xsd"
    SCHEMA_BASE_PATH = "http://site/schema/"
    RESOLVED_SCHEMA = xsdresolve.ResolvedSchema(None, SCHEMA_URL1, SCHEMA_BASE_PATH)

    def setUp(self):
        self.xsdresolver = xsdresolve.XSDSchemaResolver()
        self.resolve_patcher = mock.patch.object(self.xsdresolver, "resolve_schema", autospec=True)
        self.resolve_mock = self.resolve_patcher.start()
        self.resolve_mock.return_value = self.RESOLVED_SCHEMA

    def tearDown(self):
        self.resolve_patcher.stop()

    def test_resolve_schema(self):
        resolver = xsdresolve.XSDCachedSchemaResolver(self.xsdresolver)
        schema = resolver.resolve_schema(schema_location=self.SCHEMA_URL1)
        self.resolve_mock.assert_called_once_with(self.SCHEMA_URL1, base_path=None)
        assert_true(schema is self.RESOLVED_SCHEMA)

    def test_resolve_schema_caches_results(self):
        resolver = xsdresolve.XSDCachedSchemaResolver(self.xsdresolver)
        schema1 = resolver.resolve_schema(schema_location=self.SCHEMA_URL1)
        self.resolve_mock.reset_mock()

        schema2 = resolver.resolve_schema(schema_location=self.SCHEMA_URL1)
        assert_equals(0, self.resolve_mock.call_count)
        assert_true(schema1 is self.RESOLVED_SCHEMA)
        assert_true(schema1 is schema2)

    @mock.patch("soapfish.xsdresolve.resolve_location", autospec=True)
    def test_resolve_schema_can_match_relative_and_absolute_path(self, resolve_location_mock):
        resolve_location_mock.return_value = self.SCHEMA_URL1
        resolver = xsdresolve.XSDCachedSchemaResolver(self.xsdresolver)
        relative_url = "location1.xsd"

        schema1 = resolver.resolve_schema(schema_location=self.SCHEMA_URL1)
        self.resolve_mock.reset_mock()
        schema2 = resolver.resolve_schema(schema_location=relative_url, base_path=self.SCHEMA_BASE_PATH)

        assert_equals(0, self.resolve_mock.call_count)
        resolve_location_mock.assert_has_calls([mock.call(self.SCHEMA_URL1, base_path=None),
                                                mock.call(relative_url, base_path=self.SCHEMA_BASE_PATH)])
        assert_true(schema1 is self.RESOLVED_SCHEMA)
        assert_true(schema1 is schema2)

    def test_resolve_schema_by_namespace(self):
        resolver = xsdresolve.XSDCachedSchemaResolver(self.xsdresolver, locations={self.SCHEMA_NAMESPACE: self.SCHEMA_URL1})
        schema = resolver.resolve_schema(namespace=self.SCHEMA_NAMESPACE)
        self.resolve_mock.assert_called_with(self.SCHEMA_URL1, base_path=None)
        assert_true(schema is self.RESOLVED_SCHEMA)

    def test_resolve_schema_by_namespace_not_found(self):
        resolver = xsdresolve.XSDCachedSchemaResolver(self.xsdresolver)
        schema = resolver.resolve_schema(namespace=self.SCHEMA_NAMESPACE)
        assert_none(schema)

    def test_cache_can_be_expired(self):
        resolver = xsdresolve.XSDCachedSchemaResolver(self.xsdresolver)
        resolver.resolve_schema(schema_location=self.SCHEMA_URL1)
        resolver.resolve_schema(schema_location=self.SCHEMA_URL2)

        self.resolve_mock.reset_mock()
        assert not self.resolve_mock.called

        resolver.expire_cache()

        resolver.resolve_schema(schema_location=self.SCHEMA_URL1)
        resolver.resolve_schema(schema_location=self.SCHEMA_URL2)

        self.resolve_mock.assert_has_calls([
            mock.call(self.SCHEMA_URL1, base_path=None),
            mock.call(self.SCHEMA_URL2, base_path=None)])

    def test_cached_location_can_be_expired(self):
        resolver = xsdresolve.XSDCachedSchemaResolver(self.xsdresolver)
        resolver.resolve_schema(schema_location=self.SCHEMA_URL1)
        resolver.resolve_schema(schema_location=self.SCHEMA_URL2)

        self.resolve_mock.reset_mock()
        assert not self.resolve_mock.called

        resolver.expire_cache(self.SCHEMA_URL1)

        resolver.resolve_schema(schema_location=self.SCHEMA_URL1)
        resolver.resolve_schema(schema_location=self.SCHEMA_URL2)

        self.resolve_mock.assert_called_once_with(self.SCHEMA_URL1, base_path=None)

    def test_not_cached_location_can_be_expired(self):
        resolver = xsdresolve.XSDCachedSchemaResolver(self.xsdresolver)
        resolver.expire_cache()
        resolver.expire_cache("non/existing/location.xsd")

import mock
import os
from pythonic_testcase import (
    PythonicTestCase,
    assert_equals,
    assert_none,
    assert_not_none,
    assert_true
)
from soapfish import xsdresolve


class XSDSchemaResolverTest(PythonicTestCase):
    SCHEMA = '<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" targetNamespace="http://schema/resolver/test" />'
    SCHEMA_NAMESPACE = "http://schema/resolver/test"
    SCHEMA_FILE = os.path.abspath("some/location.xsd")
    SCHEMA_URL = "http://site/some/location.xsd"

    def setUp(self):
        self.open_document_patcher = mock.patch("soapfish.xsdresolve.utils.open_document", autospec=True)
        self.open_document_mock = self.open_document_patcher.start()
        self.open_document_mock.return_value = self.SCHEMA

    def tearDown(self):
        self.open_document_patcher.stop()

    def test_resolve_schema_from_path(self):
        resolver = xsdresolve.XSDSchemaResolver()
        schema = resolver.resolve_schema(schema_location=self.SCHEMA_FILE)
        assert_equals(self.SCHEMA_NAMESPACE, schema.targetNamespace)
        self.open_document_mock.assert_called_with(self.SCHEMA_FILE)

    def test_resolve_schema_from_relative_path(self):
        base_path = os.path.abspath("basepath")
        relative_path = "some/location.xsd"

        resolver1 = xsdresolve.XSDSchemaResolver()
        resolver2 = xsdresolve.XSDSchemaResolver(base_path=base_path)

        schema1 = resolver1.resolve_schema(schema_location=relative_path, base_path=base_path)
        schema2 = resolver2.resolve_schema(schema_location=relative_path)

        assert_equals(self.SCHEMA_NAMESPACE, schema1.targetNamespace)
        assert_equals(self.SCHEMA_NAMESPACE, schema2.targetNamespace)
        resolved_path = os.path.normpath(os.path.join(base_path, relative_path))
        self.open_document_mock.assert_has_calls([mock.call(resolved_path), mock.call(resolved_path)])

    def test_resolve_schema_from_url(self):
        resolver = xsdresolve.XSDSchemaResolver()
        schema = resolver.resolve_schema(schema_location=self.SCHEMA_URL)
        assert_equals(self.SCHEMA_NAMESPACE, schema.targetNamespace)
        self.open_document_mock.assert_called_with(self.SCHEMA_URL)

    def test_resolve_schema_by_namespace(self):
        resolver = xsdresolve.XSDSchemaResolver(locations={self.SCHEMA_NAMESPACE: self.SCHEMA_URL})
        schema = resolver.resolve_schema(namespace=self.SCHEMA_NAMESPACE)
        assert_equals(self.SCHEMA_NAMESPACE, schema.targetNamespace)
        self.open_document_mock.assert_called_with(self.SCHEMA_URL)

    def test_resolve_schema_by_namespace_not_found(self):
        resolver = xsdresolve.XSDSchemaResolver()
        schema = resolver.resolve_schema(namespace=self.SCHEMA_NAMESPACE)
        assert_none(schema)

    def test_resolve_schema_caches_results(self):
        resolver = xsdresolve.XSDSchemaResolver()
        schema1 = resolver.resolve_schema(schema_location=self.SCHEMA_URL)
        schema2 = resolver.resolve_schema(schema_location=self.SCHEMA_URL)
        assert_not_none(schema1)
        assert_true(schema1 == schema2)
        self.open_document_mock.assert_called_once_with(self.SCHEMA_URL)

    def test_cached_schema_path_is_normalized(self):
        base_path = os.path.abspath("basepath")

        resolver = xsdresolve.XSDSchemaResolver(base_path=base_path)
        resolver.resolve_schema(schema_location="some/location.xsd")
        self.open_document_mock.reset_mock()
        assert not self.open_document_mock.called

        schema = resolver.resolve_schema(schema_location="../basepath/some/location.xsd")

        assert_equals(self.SCHEMA_NAMESPACE, schema.targetNamespace)
        assert_equals(0, self.open_document_mock.call_count)

    def test_cache_can_be_expired(self):
        resolver = xsdresolve.XSDSchemaResolver()
        resolver.resolve_schema(schema_location=self.SCHEMA_FILE)
        resolver.resolve_schema(schema_location=self.SCHEMA_URL)

        self.open_document_mock.reset_mock()
        assert not self.open_document_mock.called

        resolver.expire_cache()

        resolver.resolve_schema(schema_location=self.SCHEMA_FILE)
        resolver.resolve_schema(schema_location=self.SCHEMA_URL)

        self.open_document_mock.assert_has_calls([
            mock.call(self.SCHEMA_FILE),
            mock.call(self.SCHEMA_URL)])

    def test_cached_location_can_be_expired(self):
        resolver = xsdresolve.XSDSchemaResolver()
        resolver.resolve_schema(schema_location=self.SCHEMA_FILE)
        resolver.resolve_schema(schema_location=self.SCHEMA_URL)
        self.open_document_mock.reset_mock()
        assert not self.open_document_mock.called

        resolver.expire_cache(self.SCHEMA_FILE)
        resolver.resolve_schema(schema_location=self.SCHEMA_FILE)
        resolver.resolve_schema(schema_location=self.SCHEMA_URL)

        self.open_document_mock.assert_called_once_with(self.SCHEMA_FILE)

    def test_not_cached_location_can_be_expired(self):
        resolver = xsdresolve.XSDSchemaResolver()
        resolver.expire_cache()
        resolver.expire_cache("non/existing/location.xsd")

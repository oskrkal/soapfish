from __future__ import absolute_import

from datetime import timedelta

from pythonic_testcase import PythonicTestCase, assert_equals, assert_none, assert_not_none

from soapfish.xsdresolve import ResolvedSchema
from soapfish.xsdspec import Schema
from soapfish.utils import timezone_offset_to_string, _get_element_by_name


class FormatOffsetTest(PythonicTestCase):
    def test_can_format_positive_offsets(self):
        assert_equals('+00:00', timezone_offset_to_string(timedelta(0)))
        assert_equals('+04:27', timezone_offset_to_string(timedelta(hours=4, minutes=27)))
        assert_equals('+14:00', timezone_offset_to_string(timedelta(hours=14)))

    def test_can_format_negative_offsets(self):
        assert_equals('-00:30', timezone_offset_to_string(timedelta(minutes=-30)))
        assert_equals('-01:30', timezone_offset_to_string(timedelta(minutes=-90)))
        assert_equals('-14:00', timezone_offset_to_string(timedelta(hours=-14)))


class TemplateFiltersTest(PythonicTestCase):
    SCHEMA_XML = (
        '<xs:schema targetNamespace="http://site.example/ws/spec" \n'
        '    xmlns:example="http://site.example/ws/spec" \n'
        '    xmlns:xs="http://www.w3.org/2001/XMLSchema" \n'
        '    elementFormDefault="qualified">\n'
        '    <xs:element name="title" type="xs:string" />\n'
        '    <xs:element name="contents">\n'
        '        <xs:complexType>\n'
        '            <xs:sequence>\n'
        '                <xs:element name="chapter" minOccurs="0" maxOccurs="unbounded" type="xs:string" />\n'
        '            </xs:sequence>\n'
        '        </xs:complexType>\n'
        '    </xs:element>\n'
        '</xs:schema>'
    )

    def test_can_find_element_by_name(self):
        def mock_resolver(schema_location=None, namespace=None, base_path=None):
            return None

        schema = Schema.parsexml(self.SCHEMA_XML)

        self.verify_element_is_found(schema, "title", mock_resolver)
        self.verify_element_not_found(schema, "chapter", mock_resolver)

    def test_can_find_imported_element_by_name(self):
        def mock_resolver(schema_location=None, namespace=None, base_path=None):
            assert_equals("http://localhost/ws/spec.xsd", schema_location, message="Unexpected schema location passed to mock_resolver")
            assert_equals("http://site.example/ws/spec", namespace, message="Unexpected namespace passed to mock_resolver")
            return ResolvedSchema(Schema.parsexml(self.SCHEMA_XML), schema_location, "http://localhost/ws/")

        schema = Schema.parsexml(
            '<xs:schema targetNamespace="http://site.example/ws/root" \n'
            '    xmlns:wsroot="http://site.example/ws/root" \n'
            '    xmlns:xs="http://www.w3.org/2001/XMLSchema" \n'
            '    elementFormDefault="qualified">\n'
            '    <xs:import namespace="http://site.example/ws/spec" schemaLocation="http://localhost/ws/spec.xsd"/>\n'
            '    <xs:element name="description" type="xs:string" />\n'
            '</xs:schema>'
        )

        self.verify_element_is_found(schema, "title", mock_resolver)
        self.verify_element_is_found(schema, "description", mock_resolver)
        self.verify_element_not_found(schema, "chapter", mock_resolver)


    @staticmethod
    def verify_element_is_found(schema, name, resolver):
        element = _get_element_by_name(schema, name, resolver)
        assert_not_none(element, message="element '{0}' not found".format(name))
        assert_equals(name, element.name)

    @staticmethod
    def verify_element_not_found(schema, name, resolver):
        element = _get_element_by_name(schema, name, resolver)
        assert_none(element, message="element '{0}' found but not expected".format(name))

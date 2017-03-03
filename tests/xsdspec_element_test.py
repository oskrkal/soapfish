
from nose import SkipTest
from pythonic_testcase import PythonicTestCase, assert_equals, assert_raises

from soapfish import xsd, xsdspec, xsd_types


class XSDSpecElementTest(PythonicTestCase):
    def test_can_render_simple_element(self):
        element = xsdspec.Element()
        element.name = 'Name'
        element.type = xsd_types.XSDQName(namespace='http://www.w3.org/2001/XMLSchema', localname='string')

        # WARN: this test is fragile, it relies on how lxml library renders XML
        expected_xml = b'<element xmlns:xs="http://www.w3.org/2001/XMLSchema" name="Name" type="xs:string"/>\n'
        assert_equals(expected_xml, element.xml('element'))

    def test_can_render_elements_with_anonymous_simple_types(self):
        element = xsdspec.Element()
        element.name = 'versionNumber'
        element.simpleType = xsdspec.SimpleType(
            restriction=xsdspec.Restriction(
                base=xsd_types.XSDQName(namespace='http://www.w3.org/2001/XMLSchema', localname='string'),
                pattern=xsdspec.Pattern(value='\d{2}\.\d{1,2}')
            )
        )

        # WARN: this test is fragile, it relies on how lxml library renders XML
        expected_xml = (
            b'<element name="versionNumber">\n'
            b'  <xs:simpleType xmlns:xs="http://www.w3.org/2001/XMLSchema">\n'
            b'    <xs:restriction base="xs:string">\n'
            b'      <xs:pattern value="\d{2}\.\d{1,2}"/>\n'
            b'    </xs:restriction>\n'
            b'  </xs:simpleType>\n'
            b'</element>\n'
        )
        assert_equals(expected_xml, element.xml('element'))

    def test_element_with_ref_attribute_rejects_forbidden_attributes(self):
        raise SkipTest('Elements with "ref" attribute currently do not restrict setting other attributes.')
        element = xsdspec.Element()
        element.ref = 'foo'
        element.minOccurs = 3
        element.maxOccurs = '6'
        # element.id (not present in xsdspec.Element)

        def set_(attribute, value):
            return lambda: setattr(element, attribute, value)
        assert_raises(ValueError, set_('name', u'bar'))
        assert_raises(ValueError, set_('type', u'xs:string'))
        assert_raises(ValueError, set_('nillable', u'True'))

        simple_type = xsdspec.SimpleType(restriction=xsdspec.Restriction(base='string'))
        assert_raises(ValueError, set_('simpleType', simple_type))
        # assert_raises(ValueError, set_('complexType', u'True'))

        element.ref = None
        # doesn't raise anymore because we deleted the "ref" attribute
        element.name = u'bar'

    def test_can_get_set_max_occurs_with_simple_value(self):
        xsd_element = xsdspec.Element()
        xsd_element.maxOccurs = 1
        assert_equals(1, xsd_element.maxOccurs)

    def test_can_get_set_max_occurs_with_unbounded(self):
        xsd_element = xsdspec.Element()
        xsd_element.maxOccurs = xsd.UNBOUNDED
        assert_equals(xsd.UNBOUNDED, xsd_element.maxOccurs)

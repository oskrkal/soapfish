import re
import unittest

from lxml import etree
from pythonic_testcase import assert_equals, assert_not_none
from soapfish import xsd, xsd_types


class QNameTest(unittest.TestCase):
    PREFIX1 = "fdss1"
    PREFIX2 = "fdss2"
    NS1 = "http://flightdataservices.com/schema1"
    NS2 = "http://flightdataservices.com/schema2"
    VALUE_LOCALNAME = "valtype"
    ATTR_LOCALNAME = "attrtype"
    ATTR_NAME = "attr"

    def setUp(self):
        self.element = etree.Element("someElement", nsmap={self.PREFIX1: self.NS1, self.PREFIX2: self.NS2})
        self.qname_field = xsd.QName()

    def test_parse_with_ns(self):
        self.element.text = "%s:%s" % (self.PREFIX1, self.VALUE_LOCALNAME)
        self.element.set(self.ATTR_NAME, "%s:%s" % (self.PREFIX2, self.ATTR_LOCALNAME))
        parsed_value = self.qname_field.parse_xmlelement(self.element)
        parsed_attr = self.qname_field.parse_attribute(self.element, self.ATTR_NAME)
        assert_equals(xsd_types.XSDQName(namespace=self.NS1, localname=self.VALUE_LOCALNAME), parsed_value)
        assert_equals(xsd_types.XSDQName(namespace=self.NS2, localname=self.ATTR_LOCALNAME), parsed_attr)

    def test_parse_without_ns(self):
        self.element.text = self.VALUE_LOCALNAME
        self.element.set(self.ATTR_NAME, self.ATTR_LOCALNAME)
        parsed_value = self.qname_field.parse_xmlelement(self.element)
        parsed_attr = self.qname_field.parse_attribute(self.element, self.ATTR_NAME)
        assert_equals(xsd_types.XSDQName(namespace=None, localname=self.VALUE_LOCALNAME), parsed_value)
        assert_equals(xsd_types.XSDQName(namespace=None, localname=self.ATTR_LOCALNAME), parsed_attr)

    def test_render_with_ns(self):
        self.qname_field.render(self.element, xsd_types.XSDQName(self.NS1, self.VALUE_LOCALNAME), None, None)
        self.qname_field.render_attribute(self.element, self.ATTR_NAME, xsd_types.XSDQName(self.NS2, self.ATTR_LOCALNAME))

        # prefix is determined from nsmap configured on the element
        expected_value = "%s:%s" % (self.PREFIX1, self.VALUE_LOCALNAME)
        expected_attr = "%s:%s" % (self.PREFIX2, self.ATTR_LOCALNAME)
        assert_equals(expected_value, self.element.text)
        assert_equals(expected_attr, self.element.get(self.ATTR_NAME))

    def test_render_without_ns(self):
        self.qname_field.render(self.element, xsd_types.XSDQName(None, self.VALUE_LOCALNAME), None, None)
        self.qname_field.render_attribute(self.element, self.ATTR_NAME, xsd_types.XSDQName(None, self.ATTR_LOCALNAME))
        assert_equals(self.VALUE_LOCALNAME, self.element.text)
        assert_equals(self.ATTR_LOCALNAME, self.element.get(self.ATTR_NAME))

    def test_render_with_ns_but_without_nsmap(self):
        QNAME_RE = re.compile("([^:]+):(.+)$")
        element = etree.Element("someElement", nsmap={})  # element without any namespace mappings (nsmap is empty)
        self.qname_field.render(element, xsd_types.XSDQName(self.NS1, self.VALUE_LOCALNAME), None, None)
        self.qname_field.render_attribute(element, self.ATTR_NAME, xsd_types.XSDQName(self.NS2, self.ATTR_LOCALNAME))

        value_matcher = QNAME_RE.match(element.text)
        attr_matcher = QNAME_RE.match(element.get(self.ATTR_NAME))
        element_as_str = "Actual element content: %s" % etree.tostring(element, pretty_print=True)

        assert_not_none(value_matcher, message=element_as_str)
        assert_not_none(attr_matcher, message=element_as_str)
        assert_equals(self.VALUE_LOCALNAME, value_matcher.group(2), message=element_as_str)
        assert_equals(self.NS1, element.nsmap.get(value_matcher.group(1)), message=element_as_str)
        assert_equals(self.ATTR_LOCALNAME, attr_matcher.group(2), message=element_as_str)
        assert_equals(self.NS2, element.nsmap.get(attr_matcher.group(1)), message=element_as_str)


if __name__ == "__main__":
    unittest.main()

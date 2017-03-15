# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from lxml import etree
from pythonic_testcase import PythonicTestCase

from .. import xsd

__all__ = ['SimpleTypeTestCase']


class SimpleTypeTestCase(PythonicTestCase):
    xsd_type = None

    # --- custom assertions ---------------------------------------------------
    def assert_parse(self, expected_value, string_value):
        self.assert_equals(expected_value, self._parse(string_value))

    def assert_can_set(self, value):
        class Container(xsd.ComplexType):
            foo = xsd.Element(self.xsd_type)
        container = Container()
        container.foo = value
        return container.foo

    def assert_can_not_set(self, value):
        class Container(xsd.ComplexType):
            foo = xsd.Element(self.xsd_type)
        container = Container()
        try:
            container.foo = value
        except ValueError:
            pass
        else:
            self.fail('did accept forbidden value %r' % value)

    # --- internal helpers ----------------------------------------------------
    def _parse(self, string_value):
        class Container(xsd.ComplexType):
            foo = xsd.Element(self.xsd_type)
        if string_value is None:
            string_value = ''
        xml = "<container><foo>%s</foo></container>" % string_value
        return Container.parsexml(xml).foo

    def _normalize(self, xml):
        parser = etree.XMLParser(remove_blank_text=True)
        return etree.tostring(etree.XML(xml, parser=parser))

    def parse_attribute(self, stringvalue, default=None):
        class Container(xsd.ComplexType):
            foo = xsd.Attribute(self.xsd_type, use=xsd.Use.OPTIONAL, default=default)

        xml_element = etree.Element("bar")
        if stringvalue is not None:
            xml_element.set("foo", stringvalue)
        return Container.parse_xmlelement(xml_element).foo

    def render_attribute(self, value, default=None):
        class Container(xsd.ComplexType):
            foo = xsd.Attribute(self.xsd_type, use=xsd.Use.OPTIONAL, default=default)

        c = Container(foo=value) if value is not None else Container()
        xml_element = etree.Element("bar")
        c.render(xml_element, c)
        return xml_element.get("foo")

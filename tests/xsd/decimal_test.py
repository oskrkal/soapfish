# -*- coding: utf-8 -*-

from soapfish import xsd
from soapfish.testutil import SimpleTypeTestCase


class DecimalTest(SimpleTypeTestCase):
    def test_can_restrict_acceptable_values_with_pattern(self):
        self.xsd_type = xsd.Decimal(pattern='1.')
        self.assert_can_set(12)
        self.assert_can_not_set(123)

    def test_can_parse_attribute_using_default_value(self):
        self.xsd_type = xsd.Integer
        self.assertEquals(None, self.parse_attribute(None))
        self.assertEquals(20, self.parse_attribute(None, default=20))
        self.assertEquals(10, self.parse_attribute("10", default=20))

    def test_rendering_attribute_using_default_value(self):
        self.xsd_type = xsd.Integer
        self.assertEquals(None, self.render_attribute(None))
        self.assertTrue(self.render_attribute(None, default=20) in [None, "20"])
        self.assertEquals("10", self.render_attribute(10, default=20))

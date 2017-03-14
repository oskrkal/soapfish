import unittest

from lxml import etree
from pythonic_testcase import (
    PythonicTestCase,
    assert_contains,
    assert_equals,
    assert_not_none,
)

from soapfish import testutil, utils, xsd, xsd2py, xsd_types

if not hasattr(unittest, 'skip'):
    # XXX: Skipping tests not supported in Python 2.6
    import unittest2 as unittest


class XSDReferencesCodeGenerationTest(PythonicTestCase):
    def test_can_generate_code_for_element_ref_in_the_same_schema(self):
        xsd_str = utils.open_document("tests/assets/references/elementref_same_schema.xsd")
        code = xsd2py.generate_code_from_xsd(xsd_str)

        schemas, symbols = testutil.generated_symbols(code)

        schema = next(iter(filter(self.has_target_namespace("urn:erss"), schemas)), None)

        assert_not_none(schema)
        assert_equals(xsd.ElementFormDefault.UNQUALIFIED, schema.elementFormDefault)
        assert_contains("Search", map(lambda t: t.__name__, schema.complexTypes))
        for elem in ["date", "takeoffAirport"]:
            assert_contains(elem, schema.elements, message=elem + " is missing")

        # check Search type correctness
        search = symbols["Search"](id=1, date=xsd_types.XSDDate(2017, 2, 1), takeoffAirport=["TXL", "PRG"])
        search.takeoffAirport.append("LHR")
        assert_equals(xsd_types.XSDDate(2017, 2, 1), search.date)
        assert_equals(["TXL", "PRG", "LHR"], list(search.takeoffAirport))

        # check that Search type refuses invalid values
        self.assertRaises(ValueError, setattr, search, "date", "non date value")
        self.assertRaises(ValueError, search.takeoffAirport.append, "VIE")  # 4th item; one over limit

        # check Search renders elements in correct namespace
        nsmap = {"er": "urn:erss"}
        expected_tag_names = list(map(lambda name: name % nsmap, ["id", "{%(er)s}date", "{%(er)s}takeoffAirport",
                                                                  "{%(er)s}takeoffAirport", "{%(er)s}takeoffAirport"]))
        xmlelement = etree.Element("search", nsmap=nsmap)
        search.render(xmlelement, search)
        assert_equals(expected_tag_names, list(map(lambda e: e.tag, xmlelement)))
    
    def test_can_generate_code_for_element_ref_in_different_schema(self):
        xsd_str = utils.open_document("tests/assets/references/elementref_different_schema.xsd")
        code = xsd2py.generate_code_from_xsd(xsd_str, cwd="tests/assets/references")

        schemas, symbols = testutil.generated_symbols(code)

        base_schema = next(iter(filter(self.has_target_namespace("urn:baseelement"), schemas)), None)
        child_schema = next(iter(filter(self.has_target_namespace("urn:elementref"), schemas)), None)

        # check schemas content
        assert_not_none(base_schema)
        for elem in ["landingAirport", "takeoffAirport", "pilot"]:
            assert_contains(elem, base_schema.elements, message=elem + " is missing")

        assert_not_none(child_schema)
        assert_contains("FlightType", map(lambda t: t.__name__, child_schema.complexTypes))

        # check FlightType type
        pilot = symbols["PilotType"](rank="cco", firstName="John", lastName="Doe")
        flight = symbols["FlightType"](takeoffAirport="LHR", landingAirport="PRG", pilot=[pilot])
        assert_equals("LHR", flight.takeoffAirport)
        assert_contains(pilot, flight.pilot)  # pilot member must be a list

        # check FlightType refuses invalid values
        self.assertRaises(ValueError, setattr, flight, "takeoffAirport", "NONEXISTENT")
        self.assertRaises(ValueError, flight.pilot.append, "Not a Pilot instance")

        # check FlightType renders referenced elements in correct namespace
        nsmap = {"be": "urn:baseelement", "er": "urn:elementref"}
        expected_tag_names = list(map(lambda name: name % nsmap, ["{%(be)s}takeoffAirport", "{%(be)s}landingAirport", "{%(be)s}pilot"]))
        xmlelement = etree.Element("flight", nsmap=nsmap)
        flight.render(xmlelement, flight)
        assert_equals(expected_tag_names, list(map(lambda e: e.tag, xmlelement)))

    @staticmethod
    def has_target_namespace(namespace, schema=None):
        def predicate(schema):
            return schema.targetNamespace == namespace
        return predicate if schema is None else predicate(schema)
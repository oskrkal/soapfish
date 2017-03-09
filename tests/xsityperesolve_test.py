import unittest

from pythonic_testcase import assert_equals, assert_none
from soapfish import namespaces as ns, xsd, xsd_types
from soapfish.xsityperesolve import XSITypeResolver

FDSNS1 = "http://flightdataservices.com/ns1"
FDSNS2 = "http://flightdataservices.com/ns2"
FDSNS3 = "http://flightdataservices.com/ns3"


# Model -------------------

AIRPORT_XSITYPE = xsd_types.XSDQName(FDSNS1, "airport")
FLIGHT_XSITYPE = xsd_types.XSDQName(FDSNS1, "flight")
FLIGHTNUM_SIMPLE_XSITYPE = xsd_types.XSDQName(FDSNS1, "flightNumber")
RANK_SIMPLE_XSITYPE = xsd_types.XSDQName(FDSNS2, "rank")
PILOT_XSITYPE = xsd_types.XSDQName(FDSNS2, "pilot")
UNKNOWN_LOCALTYPE = xsd_types.XSDQName(FDSNS1, "unknown")
UNKNOWN_NAMESPACETYPE = xsd_types.XSDQName("urn:unknown", AIRPORT_XSITYPE.localname)


class Airport(xsd.ComplexType):
    XSI_TYPE = AIRPORT_XSITYPE
    type = xsd.Element(xsd.String, namespace=FDSNS1)
    code = xsd.Element(xsd.String, namespace=FDSNS1)


class FlightNumber(xsd.String):
    XSI_TYPE = FLIGHTNUM_SIMPLE_XSITYPE


class Flight(xsd.ComplexType):
    XSI_TYPE = FLIGHT_XSITYPE
    takeoff_datetime = xsd.Element(xsd.DateTime, minOccurs=0, namespace=FDSNS1)
    takeoff_airport = xsd.Element(Airport, namespace=FDSNS1)
    landing_airport = xsd.Element(Airport, namespace=FDSNS1)


class Rank(xsd.String):
    XSI_TYPE = RANK_SIMPLE_XSITYPE

    def __init__(self):
        super(Rank, self).__init__(enumeration=["CAPTAIN", "FIRST_OFFICER"])


class Pilot(xsd.ComplexType):
    XSI_TYPE = PILOT_XSITYPE
    rank = xsd.Attribute(Rank)
    first_name = xsd.Element(xsd.String, namespace=FDSNS2)
    last_name = xsd.Element(xsd.String, namespace=FDSNS2)


FDSNS1_SCHEMA = xsd.Schema(FDSNS1, elementFormDefault=xsd.ElementFormDefault.QUALIFIED,
                           complexTypes=[Airport])

FDSNS2_SCHEMA = xsd.Schema(FDSNS2, elementFormDefault=xsd.ElementFormDefault.QUALIFIED,
                           simpleTypes=[Rank], complexTypes=[Pilot])

PARENT_SCHEMA = xsd.Schema(FDSNS1, elementFormDefault=xsd.ElementFormDefault.QUALIFIED,
                           simpleTypes=[FlightNumber], complexTypes=[Flight],
                           imports=[FDSNS2_SCHEMA], includes=[FDSNS1_SCHEMA])


# Test classes ------------

class XSITypeResolverTest(unittest.TestCase):
    def setUp(self):
        self.resolver = XSITypeResolver([PARENT_SCHEMA])

    def test_can_return_resolvable_namespaces(self):
        namespaces = sorted(self.resolver.resolvable_namespaces())
        expected = sorted([FDSNS1, FDSNS2])
        assert_equals(expected, namespaces)

    def test_can_resolve_complex_type(self):
        assert_equals(Flight, self.resolver.find_type(FLIGHT_XSITYPE))

    def test_can_resolve_complex_type_from_imported_schema(self):
        assert_equals(Pilot, self.resolver.find_type(PILOT_XSITYPE))

    def test_can_resolve_complex_type_from_included_schema(self):
        assert_equals(Airport, self.resolver.find_type(AIRPORT_XSITYPE))

    def test_can_resolve_simple_type(self):
        assert_equals(FlightNumber, self.resolver.find_type(FLIGHTNUM_SIMPLE_XSITYPE))

    def test_can_resolve_simple_type_from_imported_schema(self):
        assert_equals(Rank, self.resolver.find_type(RANK_SIMPLE_XSITYPE))

    def test_returns_none_for_unknown_type(self):
        assert_none(self.resolver.find_type(UNKNOWN_LOCALTYPE))

    def test_returns_none_for_known_localname_but_unknown_namespace(self):
        assert_none(self.resolver.find_type(UNKNOWN_LOCALTYPE))


class XSITypeResolverWithMultipleSchemasTest(unittest.TestCase):
    def setUp(self):
        self.resolver = XSITypeResolver([FDSNS1_SCHEMA, FDSNS2_SCHEMA])

    def test_can_return_resolvable_namespaces(self):
        namespaces = sorted(self.resolver.resolvable_namespaces())
        expected = sorted([FDSNS1, FDSNS2])
        assert_equals(expected, namespaces)

    def test_can_resolve_types_from_both_schemas(self):
        assert_equals(Airport, self.resolver.find_type(AIRPORT_XSITYPE))  # in schema 1
        assert_equals(Pilot, self.resolver.find_type(PILOT_XSITYPE))      # in schema 2

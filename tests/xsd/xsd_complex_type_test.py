import unittest
from pythonic_testcase import assert_equals, assert_not_none, assert_true
from lxml import etree
from soapfish import xsd, xsdspec, xsd_types, namespaces as ns


# Test schema definition ------------------------
URN_BASE = "urn:base"
URN_FLIGHTS = "urn:flights"
URN_PERSON = "urn:person"


class BaseRequest(xsd.ComplexType):
    XSI_TYPE = xsd_types.XSDQName(URN_BASE, "baseRequest")
    uuid = xsd.Element(xsd.String)


class Query(xsd.ComplexType):
    maxRows = xsd.Attribute(xsd.Integer, default=20)
    searchRequest = xsd.Element(BaseRequest)


class Person(xsd.ComplexType):
    XSI_TYPE = xsd_types.XSDQName(URN_PERSON, "person")
    personalNo = xsd.Attribute(xsd.Int, use=xsd.Use.OPTIONAL)
    firstName = xsd.Element(xsd.String)
    lastName = xsd.Element(xsd.String)


class Airport(xsd.ComplexType):
    XSI_TYPE = xsd_types.XSDQName(URN_FLIGHTS, "airport")
    type = xsd.Element(xsd.String)
    code = xsd.Element(xsd.String)


class FlightSearch(BaseRequest):
    XSI_TYPE = xsd_types.XSDQName(URN_FLIGHTS, "flightSearch")
    INHERITANCE = xsd.Inheritance.EXTENSION
    flightNumber = xsd.Element(xsd.String)


class Pilot(Person):
    XSI_TYPE = xsd_types.XSDQName(URN_FLIGHTS, "pilot")
    licenseNo = xsd.Element(xsd.String)


BASE_SCHEMA = xsd.Schema(URN_BASE,
                         elementFormDefault=xsd.ElementFormDefault.QUALIFIED,
                         complexTypes=[BaseRequest, Query])

PERSON_SCHEMA = xsd.Schema(URN_PERSON,
                           elementFormDefault=xsd.ElementFormDefault.UNQUALIFIED,  # to test unqualified nested elements
                           complexTypes=[Person])

FLIGHT_SCHEMA = xsd.Schema(URN_FLIGHTS,
                           elementFormDefault=xsd.ElementFormDefault.QUALIFIED,
                           complexTypes=[Airport, FlightSearch, Pilot])


# Tests -----------------------------------------

class ComplexTypeWithNSTest(unittest.TestCase):
    def test_render_complex_type_with_qualified_elements(self):
        nsmap = {"fs": URN_FLIGHTS}
        airport = Airport(type="IATA", code="WAW")

        xmlelement = etree.Element("takeoff_airport", nsmap=nsmap)
        airport.render(xmlelement, airport)
        actual_xml_msg = "Actual xml: " + etree.tounicode(xmlelement, pretty_print=True)

        type = xmlelement.find("./{%(fs)s}type" % nsmap)
        code = xmlelement.find("./{%(fs)s}code" % nsmap)

        assert_not_none(type, message=actual_xml_msg)
        assert_equals("IATA", type.text, message=actual_xml_msg)
        assert_not_none(code, message=actual_xml_msg)
        assert_equals("WAW", code.text, message=actual_xml_msg)

    def test_render_complex_type_with_unqualified_elements(self):
        nsmap = {"bs": URN_BASE, "fs": URN_FLIGHTS, "pn": URN_PERSON}
        pilot = Pilot(firstName="Tom", lastName="Kazansky", licenseNo="123456F")

        xmlelement = etree.Element("pilot", nsmap=nsmap)
        pilot.render(xmlelement, pilot)
        actual_xml_msg = "Actual xml: " + etree.tounicode(xmlelement, pretty_print=True)

        license_no = xmlelement.find("./{%(fs)s}licenseNo" % nsmap)
        last_name = xmlelement.find("./lastName")  # lastName is unqualified

        assert_not_none(license_no, message=actual_xml_msg)
        assert_not_none(last_name, message=actual_xml_msg)

    def test_render_complex_type_with_element_in_different_ns(self):
        query = Query(searchRequest=FlightSearch(uuid="1234-aedf-5678", flightNumber="FL-1234"))
        nsmap = {"bs": URN_BASE, "fs": URN_FLIGHTS}

        xmlelement = etree.Element("query", nsmap=nsmap)
        query.render(xmlelement, query)
        actual_xml_msg = "Actual xml: " + etree.tounicode(xmlelement, pretty_print=True)

        searchRequest = xmlelement.find("./{%(bs)s}searchRequest" % nsmap)
        uuid = xmlelement.find("./{%(bs)s}searchRequest/{%(bs)s}uuid" % nsmap)
        flightNumber = xmlelement.find("./{%(bs)s}searchRequest/{%(fs)s}flightNumber" % nsmap)

        assert_not_none(searchRequest, message=actual_xml_msg)
        assert_true(uuid is not None and uuid.text == "1234-aedf-5678", message=actual_xml_msg)
        assert_true(flightNumber is not None and flightNumber.text == "FL-1234", message=actual_xml_msg)

    def test_tagname_parsexml(self):
        class TestType(xsd.ComplexType):
            foo = xsd.Element(xsd.String, tagname='bar')
        SCHEMA = xsd.Schema("urn:ns", complexTypes=[TestType], elementFormDefault=xsd.ElementFormDefault.QUALIFIED)
        xml = b"<T xmlns:ns=\"urn:ns\"><ns:bar>coucou</ns:bar></T>"

        obj = TestType.parsexml(xml)
        self.assertEquals('coucou', obj.foo)

    def test_tagname_render(self):
        class TestType(xsd.ComplexType):
            foo = xsd.Element(xsd.String, tagname='bar')
        SCHEMA = xsd.Schema("urn:ns", complexTypes=[TestType], elementFormDefault=xsd.ElementFormDefault.QUALIFIED)

        obj = TestType(foo='coucou')
        xmlelement = etree.Element("T")
        obj.render(xmlelement, obj)

        bar_element = xmlelement[0]
        assert_equals("{urn:ns}bar", bar_element.tag)
        assert_equals("coucou", bar_element.text)

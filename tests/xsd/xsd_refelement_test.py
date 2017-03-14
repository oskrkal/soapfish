import six
import unittest
from lxml import etree
from pythonic_testcase import assert_equals, assert_is_empty, assert_isinstance, assert_length, assert_true

from soapfish import namespaces as ns, xsd, xsd_types, xsityperesolve


# Test document model -------------------------

# urn:baseelement schema

class AirportCode(xsd.String):
    XSI_TYPE = xsd_types.XSDQName("urn:baseelement", "airportCode")
    def __init__(self):
        super(AirportCode, self).__init__(enumeration=["LHR", "PRG", "TXL"])


class RankType(xsd.String):
    XSI_TYPE = xsd_types.XSDQName("urn:baseelement", "rankType")
    def __init__(self):
        super(RankType, self).__init__(enumeration=["cfo", "ccapt", "cscapt", "cco"])


class PilotType(xsd.ComplexType):
    XSI_TYPE = xsd_types.XSDQName("urn:baseelement", "pilotType")
    suspended = xsd.Attribute(xsd.Boolean, use=xsd.Use.OPTIONAL, default=False)
    rank = xsd.Element(RankType)
    firstName = xsd.Element(xsd.String)
    lastName = xsd.Element(xsd.String)

Schema_urn_baseelement = xsd.Schema("urn:baseelement", elementFormDefault=xsd.ElementFormDefault.QUALIFIED,
                                    simpleTypes=[AirportCode, RankType], complexTypes=[PilotType],
                                    elements={"takeoffAirport": xsd.Element(AirportCode), "landingAirport": xsd.Element(AirportCode),
                                              "pilot": xsd.Element(PilotType)})


# urn:elementref schema

class LineType(xsd.ComplexType):
    XSI_TYPE = xsd_types.XSDQName("urn:elementref", "lineType")
    takeoffAirportRef = xsd.RefElement(Schema_urn_baseelement.get_element_by_name("takeoffAirport"))
    landingAirportRef = xsd.RefElement(Schema_urn_baseelement.get_element_by_name("landingAirport"))
    flightsAYear = xsd.Element(xsd.Integer)


class PilotsList(xsd.ComplexType):
    XSI_TYPE = xsd_types.XSDQName("urn:elementref", "pilotsList")
    pilots = xsd.RefElement(Schema_urn_baseelement.get_element_by_name("pilot"), minOccurs=0, maxOccurs=xsd.UNBOUNDED)


class ExtendedLineType(LineType):
    XSI_TYPE = xsd_types.XSDQName("urn:elementref", "extnededLineType")
    planeTypes = xsd.ListElement(xsd.String, "planeType", minOccurs=1, maxOccurs=xsd.UNBOUNDED)


class ExtendedPilotType(PilotType):
    XSI_TYPE = xsd_types.XSDQName("urn:elementref", "extendedPilotType")
    hireDate = xsd.Element(xsd.Date)

Schema_urn_elementref = xsd.Schema("urn:elementref", elementFormDefault=xsd.ElementFormDefault.QUALIFIED,
                                   imports=[Schema_urn_baseelement],
                                   complexTypes=[LineType, PilotsList, ExtendedLineType, ExtendedPilotType],
                                   elements={"line": xsd.Element(LineType), "pilots": xsd.Element(PilotsList)})


# Test cases ----------------------------------

NSMAP = {"er": Schema_urn_elementref.targetNamespace,
         "be": Schema_urn_baseelement.targetNamespace}


class RefElementRenderTest(unittest.TestCase):
    def test_can_render_element_ref(self):
        line = LineType(takeoffAirportRef="LHR", landingAirportRef="PRG", flightsAYear=50)

        xmlelement = etree.Element("{%s}line" % Schema_urn_elementref.targetNamespace, nsmap=NSMAP)
        line.render(xmlelement, line)
        actual_xml = "Actual XML: " + etree.tounicode(xmlelement)

        assert_equals("LHR", xmlelement.findtext("{%(be)s}takeoffAirport" % NSMAP), message=actual_xml)
        assert_equals("PRG", xmlelement.findtext("{%(be)s}landingAirport" % NSMAP), message=actual_xml)

    def test_can_render_element_ref_list(self):
        pilots_list = PilotsList(pilots=[PilotType(rank="cfo", firstName="John", lastName="Doe"),
                                         PilotType(rank="ccapt", firstName="Patrick", lastName="House")])

        xmlelement = etree.Element("{%s}pilots" % Schema_urn_elementref.targetNamespace, nsmap=NSMAP)
        pilots_list.render(xmlelement, pilots_list)
        actual_xml = "Actual XML: " + etree.tounicode(xmlelement)

        pilots = xmlelement.findall("{%(be)s}pilot" % NSMAP)
        assert_length(2, pilots, message=actual_xml)
        self.check_element_children(self.expected_pilot("cfo", "John", "Doe"), pilots[0])
        self.check_element_children(self.expected_pilot("ccapt", "Patrick", "House"), pilots[1])

    def test_can_render_empty_element_ref_list(self):
        pilots_list = PilotsList(pilots=[])

        xmlelement = etree.Element("{%s}pilots" % Schema_urn_elementref.targetNamespace, nsmap=NSMAP)
        pilots_list.render(xmlelement, pilots_list)
        actual_xml = "Actual XML: " + etree.tounicode(xmlelement)

        assert_is_empty(xmlelement, message=actual_xml)

    def test_can_render_inherited_element_ref(self):
        line = ExtendedLineType(takeoffAirportRef="LHR", landingAirportRef="PRG", flightsAYear=50, planeTypes=["A319", "A320"])

        xmlelement = etree.Element("{%s}line" % Schema_urn_elementref.targetNamespace, nsmap=NSMAP)
        line.render(xmlelement, line)
        actual_xml = "Actual XML: " + etree.tounicode(xmlelement)

        assert_equals("LHR", xmlelement.findtext("{%(be)s}takeoffAirport" % NSMAP), message=actual_xml)
        assert_equals("PRG", xmlelement.findtext("{%(be)s}landingAirport" % NSMAP), message=actual_xml)
        assert_equals(["A319", "A320"], list(map(lambda e: e.text, xmlelement.iterfind("{%(er)s}planeType" % NSMAP))), message=actual_xml)

    def test_can_render_element_ref_with_value_of_derived_type(self):
        pilots_list = PilotsList(pilots=[ExtendedPilotType(rank="cfo", firstName="John", lastName="Doe", hireDate=xsd_types.XSDDate(2017, 2, 1))])

        xmlelement = etree.Element("{%s}pilots" % Schema_urn_elementref.targetNamespace, nsmap=NSMAP)
        pilots_list.render(xmlelement, pilots_list)
        actual_xml = "Actual XML: " + etree.tounicode(xmlelement)

        pilots = xmlelement.findall("{%(be)s}pilot" % NSMAP)
        assert_length(1, pilots, message=actual_xml)
        assert_equals("er:extendedPilotType", pilots[0].get("{%s}type" % ns.xsi), message=actual_xml)
        assert_equals("2017-02-01", pilots[0].findtext("{%(er)s}hireDate" % NSMAP), message=actual_xml)

    @staticmethod
    def check_element_children(expected, actual):
        message = "element: %s; actual content: " + etree.tounicode(actual)
        for tagname, expected_text in six.iteritems(expected):
            assert_equals(expected_text, actual.findtext(tagname), message=message % tagname)

    @staticmethod
    def expected_pilot(rank, firstName, lastName):
        return {
            "{%(be)s}rank" % NSMAP: rank,
            "{%(be)s}firstName" % NSMAP: firstName,
            "{%(be)s}lastName" % NSMAP: lastName
        }


class RefElementParseTest(unittest.TestCase):
    def test_can_parse_element_ref(self):
        line_xml = ('<line xmlns="urn:elementref" xmlns:be="urn:baseelement">\n'
                    '    <be:takeoffAirport>TXL</be:takeoffAirport>\n'
                    '    <be:landingAirport>LHR</be:landingAirport>\n'
                    '    <flightsAYear>50</flightsAYear>\n'
                    '</line>')
        line = LineType.parsexml(line_xml)

        assert_equals("TXL", line.takeoffAirportRef)
        assert_equals("LHR", line.landingAirportRef)
        assert_equals(50, line.flightsAYear)
        
    def test_can_parse_element_ref_list(self):
        pilots_xml = ('<pilots xmlns="urn:elementref" xmlns:be="urn:baseelement">\n'
                      '    <be:pilot>\n'
                      '        <be:rank>cfo</be:rank>\n'
                      '        <be:firstName>John</be:firstName>\n'
                      '        <be:lastName>Doe</be:lastName>\n'
                      '    </be:pilot>\n'
                      '    <be:pilot>\n'
                      '        <be:rank>ccapt</be:rank>\n'
                      '        <be:firstName>Patrick</be:firstName>\n'
                      '        <be:lastName>House</be:lastName>\n'
                      '    </be:pilot>\n'
                      '</pilots>')
        pilots_list = PilotsList.parsexml(pilots_xml)

        assert_length(2, pilots_list.pilots)
        self.check_pilot(self.expected_pilot("cfo", "John", "Doe"), pilots_list.pilots[0])
        self.check_pilot(self.expected_pilot("ccapt", "Patrick", "House"), pilots_list.pilots[1])

    def test_can_parse_empty_element_ref_list(self):
        pilots_xml = ('<pilots xmlns="urn:elementref" xmlns:be="urn:baseelement"/>')
        pilots_list = PilotsList.parsexml(pilots_xml)

        assert_is_empty(pilots_list.pilots)

    def test_can_parse_inherited_element_ref(self):
        line_xml = ('<line xmlns="urn:elementref" xmlns:be="urn:baseelement">\n'
                    '    <be:takeoffAirport>TXL</be:takeoffAirport>\n'
                    '    <be:landingAirport>LHR</be:landingAirport>\n'
                    '    <flightsAYear>50</flightsAYear>\n'
                    '    <planeType>A319</planeType>\n'
                    '    <planeType>A320</planeType>\n'
                    '</line>')
        line = ExtendedLineType.parsexml(line_xml)

        assert_equals("TXL", line.takeoffAirportRef)
        assert_equals("LHR", line.landingAirportRef)
        assert_equals(50, line.flightsAYear)
        assert_equals(["A319", "A320"], line.planeTypes)

    def test_can_parse_element_ref_with_value_of_derived_type(self):
        pilots_xml = ('<er:pilots xmlns:er="urn:elementref" xmlns:be="urn:baseelement" \n'
                      '           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n'
                      '    <be:pilot xsi:type="er:extendedPilotType">\n'
                      '        <be:rank>cfo</be:rank>\n'
                      '        <be:firstName>John</be:firstName>\n'
                      '        <be:lastName>Doe</be:lastName>\n'
                      '        <er:hireDate>2017-02-01</er:hireDate>\n'
                      '    </be:pilot>\n'
                      '</er:pilots>')
        pilots_list = PilotsList.parsexml(pilots_xml, type_resolver=xsityperesolve.XSITypeResolver([Schema_urn_elementref]))
        actual_pilots = "actual pilots list: " + str(pilots_list)

        assert_length(1, pilots_list.pilots, message=actual_pilots)
        pilot = pilots_list.pilots[0]
        assert_isinstance(pilot, ExtendedPilotType, message=actual_pilots)
        self.check_pilot(self.expected_pilot("cfo", "John", "Doe", hireDate=xsd_types.XSDDate(2017, 2, 1)), pilot)


    @staticmethod
    def check_pilot(expected, actual):
        message = "attr %s does not match; actual pilot: " + str(actual)
        for attr, expected_value in six.iteritems(expected):
            assert_true(hasattr(actual, attr), message="attr %s is missing" % attr)
            assert_equals(expected_value, getattr(actual, attr), message=message % attr)
            
    @staticmethod
    def expected_pilot(rank, firstName, lastName, **kwargs):
        return dict(rank=rank, firstName=firstName, lastName=lastName, **kwargs)

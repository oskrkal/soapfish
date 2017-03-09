# -*- coding: utf-8 -*-

from . import namespaces as ns, xsd, xsd_types

ENVELOPE_NAMESPACE = ns.soap12_envelope
BINDING_NAMESPACE = ns.wsdl_soap12
CONTENT_TYPE = 'application/soap+xml'
NAME = 'soap12'


# --- Functions ---------------------------------------------------------------
def determine_soap_action(request):
    content_types = request.environ.get('CONTENT_TYPE', '').split(';')
    for content_type in content_types:
        if content_type.strip(' ').startswith('action='):
            action = content_type.split('=')[1]
            return action.replace('"', '')
    return None


def build_http_request_headers(soapAction):
    return {'content-type': CONTENT_TYPE + ';action="%s"' % soapAction}


def get_error_response(code, message, actor=None, header=None):
    return Envelope.error_response(code, message, actor=actor, header=header)


def parse_fault_message(fault):
    return fault.Code.Value, fault.Reason.Text, fault.Role


class Header(xsd.ComplexType):
    '''
    SOAP Envelope Header.
    '''
    # NOTE: implementation was copied from soap11.Header; it could not be inherited, because
    # Header type in SOAP 1.2 scheme actually does not extend Header from SOAP 1.1
    def accept(self, value):
        return value

    def parse_as(self, ContentType, type_resolver=None):
        return ContentType.parse_xmlelement(self._xmlelement, type_resolver=type_resolver)

    def render(self, parent, instance, namespace=None, elementFormDefault=None):
        return super(Header, self).render(parent, instance, namespace=instance.SCHEMA.targetNamespace,
                                          elementFormDefault=elementFormDefault)


class Code(xsd.ComplexType):
    CLIENT = xsd_types.XSDQName(ENVELOPE_NAMESPACE, 'Sender')
    SERVER = xsd_types.XSDQName(ENVELOPE_NAMESPACE, 'Receiver')
    Value = xsd.Element(xsd.QName)


class LanguageString(xsd.String):

    def render(self, parent, value, namespace, elementFormDefault):
        parent.text = self.xmlvalue(value, parent)
        parent.set('{%s}lang' % ns.xml, 'en')


class Reason(xsd.ComplexType):
    Text = xsd.Element(LanguageString)


class Fault(xsd.ComplexType):
    '''
    SOAP Envelope Fault.
    '''
    Code = xsd.Element(Code)
    Reason = xsd.Element(Reason)
    Role = xsd.Element(xsd.String, minOccurs=0)


class Body(xsd.ComplexType):
    '''
    SOAP Envelope Body.
    '''
    # NOTE: implementation was copied from soap11.Body; it could not be inherited, because
    # Body type in SOAP 1.2 scheme actually does not extend Body from SOAP 1.1. If soap12.Body
    # was derived from soap11.Body, the message and Fault elements would be in soap11 namespace
    # which is incorrect.
    message = xsd.ClassNamedElement(xsd.NamedType, minOccurs=0)
    Fault = xsd.Element(Fault, minOccurs=0)

    def parse_as(self, ContentType, type_resolver=None):
        return ContentType.parse_xmlelement(self._xmlelement[0], type_resolver=type_resolver)

    def content(self):
        return self._xmlelement[0]


class Envelope(xsd.ComplexType):
    '''
    SOAP Envelope.
    '''
    Header = xsd.Element(Header, nillable=True)
    Body = xsd.Element(Body)

    @classmethod
    def response(cls, tagname, return_object, header=None):
        envelope = cls()
        if header is not None:
            envelope.Header = header
        envelope.Body = Body()
        envelope.Body.message = xsd.NamedType(name=tagname, value=return_object)
        return envelope.xml('Envelope', namespace=ENVELOPE_NAMESPACE,
                            elementFormDefault=xsd.ElementFormDefault.QUALIFIED, pretty_print=False)

    @classmethod
    def error_response(cls, code, message, header=None, actor=None):
        envelope = cls()
        if header is not None:
            envelope.Header = header
        envelope.Body = Body()
        code = Code(Value=code)
        reason = Reason(Text=message)
        envelope.Body.Fault = Fault(Code=code, Reason=reason, Role=actor)
        return envelope.xml('Envelope', namespace=ENVELOPE_NAMESPACE,
                            elementFormDefault=xsd.ElementFormDefault.QUALIFIED, pretty_print=False)


SCHEMA = xsd.Schema(
    targetNamespace=ENVELOPE_NAMESPACE,
    elementFormDefault=xsd.ElementFormDefault.QUALIFIED,
    complexTypes=[Header, Body, Envelope, Code, Reason, Fault],
)

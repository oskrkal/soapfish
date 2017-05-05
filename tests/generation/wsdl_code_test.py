import os
import mock
import unittest

from pythonic_testcase import (
    PythonicTestCase,
    assert_equals,
    assert_is_not_empty,
    assert_isinstance,
    assert_length,
    assert_not_none,
    assert_true,
)

from soapfish import utils, wsdl2py, xsd
from soapfish.testutil import generated_symbols

if not hasattr(unittest, 'skip'):
    # XXX: Skipping tests not supported in Python 2.6
    import unittest2 as unittest


class WSDLCodeGenerationTest(PythonicTestCase):

    def test_can_generate_code_for_simple_wsdl_import(self):
        path = 'tests/assets/generation/import_simple.wsdl'
        xml = utils.open_document(path)
        code = wsdl2py.generate_code_from_wsdl(xml, 'client', cwd=os.path.dirname(path))
        schemas, symbols = generated_symbols(code)
        assert_is_not_empty(schemas)

    def test_can_generate_code_for_nested_wsdl_import(self):
        path = 'tests/assets/generation/import_nested.wsdl'
        xml = utils.open_document(path)
        code = wsdl2py.generate_code_from_wsdl(xml, 'client', cwd=os.path.dirname(path))
        schemas, symbols = generated_symbols(code)
        assert_is_not_empty(schemas)

    def test_can_generate_code_for_looped_wsdl_import(self):
        path = 'tests/assets/generation/import_looped.wsdl'
        xml = utils.open_document(path)
        code = wsdl2py.generate_code_from_wsdl(xml, 'client', cwd=os.path.dirname(path))
        schemas, symbols = generated_symbols(code)
        assert_is_not_empty(schemas)

    def test_can_generate_code_for_two_schemas(self):
        xml = utils.open_document('tests/assets/generation/multi_schema.wsdl')
        code = wsdl2py.generate_code_from_wsdl(xml, 'client')
        schemas, symbols = generated_symbols(code)
        assert_is_not_empty(schemas)
        assert_length(2, [s for s in symbols if s.startswith('Schema_')])
        assert_equals(['A'], list(schemas[0].elements))
        assert_equals(['B'], list(schemas[1].elements))

    @unittest.skip('Cannot generate code for wsdl with type inheritance')
    def test_can_generate_code_for_inheritance(self):
        xml = utils.open_document('tests/assets/generation/inheritance.wsdl')
        code = wsdl2py.generate_code_from_wsdl(xml, 'client')
        schemas, symbols = generated_symbols(code)
        assert_is_not_empty(schemas)
        assert_length(4, symbols)
        assert_equals(['B', 'A'], list(schemas[0].elements))
        assert_isinstance(schemas[0].elements['B']._type, xsd.String)
        assert_isinstance(schemas[0].elements['A']._type, schemas[0].elements['B']._type.__class__)

    def test_can_generate_remote_tree(self):
        def _mock(path):
            if path == 'http://example.org/xsd/simple_element.xsd':
                filename = 'tests/assets/generation/simple_element.xsd'
            else:
                self.fail("Unexpected remote path: %s" % path)

            with open(filename, 'rb') as f:
                return f.read()

        xml = utils.open_document('tests/assets/generation/import_remote.wsdl')
        with mock.patch('soapfish.xsdresolve.utils.open_document') as p:
            p.side_effect = _mock
            code = wsdl2py.generate_code_from_wsdl(
                xml,
                'client',
                cwd='http://example.org/code/')
            schemas, symbols = generated_symbols(code)

    def test_can_generate_code_for_wsdl_importing_schema_and_using_soap_headers(self):
        path = 'tests/assets/include/include_with_soap_headers.wsdl'
        xml = utils.open_document(path)
        code = wsdl2py.generate_code_from_wsdl(xml, 'client', cwd=os.path.dirname(path))
        schemas, symbols = generated_symbols(code)
        flight_search_method = symbols.get("flightSearch_method")
        assert_not_none(flight_search_method)
        assert_true(hasattr(flight_search_method.input_header, 'credentials'))
        assert_true(hasattr(flight_search_method.output_header, 'serviceInfo'))


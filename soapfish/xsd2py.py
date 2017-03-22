#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import argparse
import functools
import itertools
import logging
import os
import sys

import six
from lxml import etree

from . import xsdspec, xsd_types, xsdresolve
from .utils import get_rendering_environment

logger = logging.getLogger('soapfish')


# --- Helpers -----------------------------------------------------------------
def rewrite_paths(schema, base_path):
    """
    Rewrite include and import locations relative to base_path.

    This location is the unique identification for each file, they must match.
    """
    for i in itertools.chain(schema.includes, schema.imports):
        if i.schemaLocation is None or '://' in i.schemaLocation:
            # skip if nothing to rewrite or absolute url.
            continue
        elif '://' in base_path:
            # remote files must handle paths as url.
            i.schemaLocation = six.moves.urllib.parse.urljoin(base_path, i.schemaLocation)
        else:
            # local files should handle relative paths.
            path = os.path.normpath(os.path.join(base_path, i.schemaLocation))
            i.schemaLocation = os.path.relpath(path, base_path)


def resolve_import(i, known_paths, known_types, parent_namespace, base_path, resolver):
    assert isinstance(i, (xsdspec.Import, xsdspec.Include))
    tag = i.__class__.__name__.lower()
    logger.debug('Resolving import xsd:%s=%s (base_path=%s)' % (tag, i.schemaLocation, base_path))
    return generate_code_from_xsd_file(i.schemaLocation, resolver, base_path=base_path, known_paths=known_paths,
                                       known_types=known_types, parent_namespace=parent_namespace, encoding=None)


def generate_code_from_xsd_file(location, resolver, base_path=None, known_paths=None,
                                known_types=None, parent_namespace=None, encoding='utf8'):
    schema_location = xsdresolve.resolve_location(location, base_path)
    if schema_location and schema_location in (known_paths or []):
        logger.info('Code for XSD location %s already generated; skipping.' % schema_location)
        return ''

    resolved_schema = resolver.resolve_schema(schema_location=location, base_path=base_path)

    logger.info('Generating code for XSD location %s' % resolved_schema.location)
    return generate_code_from_schema(resolved_schema, known_paths=known_paths, known_types=known_types,
                 parent_namespace=parent_namespace, encoding=encoding, standalone=False, resolver=resolver)


def generate_code_from_xsd(xml, known_paths=None, known_types=None,
                           location=None, parent_namespace=None,
                           encoding='utf8', base_path=None,
                           standalone=True, resolver=None):

    if isinstance(xml, six.binary_type):
        xml = etree.fromstring(xml)

    if known_paths is None:
        known_paths = []

    # Skip if this file has already been included:
    if location and location in known_paths:
        return ''

    schema = xsdspec.Schema.parse_xmlelement(xml)

    logger.info('Generating code for XSD schema for target namespace %s' % schema.targetNamespace)
    return generate_code_from_schema(xsdresolve.ResolvedSchema(schema, location, base_path), known_paths=known_paths, known_types=known_types,
                                     parent_namespace=parent_namespace, encoding=encoding, standalone=standalone, resolver=resolver)


def generate_code_from_schema(resolved_schema, known_paths=None, known_types=None,
                 parent_namespace=None, encoding=None, standalone=False, resolver=None):
    code = schema_to_py(resolved_schema.schema, known_paths, known_types,
                        resolved_schema.location, base_path=resolved_schema.base_path,
                        standalone=standalone, resolver=resolver)
    return code.encode(encoding) if encoding else code


def _reorder_complexTypes(schema):
    """
    Reorder complexTypes to render base extension/restriction elements
    render before the children.
    """
    weights = {}
    tns = schema.targetNamespace
    for n, complex_type in enumerate(schema.complexTypes):
        content = complex_type.complexContent
        if content:
            extension = content.extension
            restriction = content.restriction
            if extension:
                base = extension.base
            elif restriction:
                base = restriction.base
            if base and base.namespace is None:
                base = xsd_types.XSDQName(tns, base.localname)
        else:
            base = None

        weights[(tns, complex_type.name)] = (n, base)

    def _cmp(a, b):
        def get_qname(type_or_qname):
            name = getattr(type_or_qname, 'name', None)
            return (tns, name) if name is not None else type_or_qname

        def is_extension(obj, base):
            return base and obj == base

        def is_known_type(qname):
            return qname and (qname in weights)

        a = get_qname(a)
        b = get_qname(b)

        w_a, base_a = weights[a]
        w_b, base_b = weights[b]
        # a is a extension/restriction of b: a > b
        if is_extension(b, base_a):
            return 1
        # b is a extension/restriction of a: a < b
        elif is_extension(a, base_b):
            return -1
        # a and b are not extension/restriction or extend/restrict a type defined outside of this schema
        elif not is_known_type(base_a) and not is_known_type(base_b):
            return w_a - w_b
        # inconclusive, do the same test with their bases
        return _cmp(base_a if is_known_type(base_a) else a,
                    base_b if is_known_type(base_b) else b)

    if hasattr(functools, 'cmp_to_key'):
        kw = {'key': functools.cmp_to_key(_cmp)}
    else:
        kw = {'cmp': _cmp}  # XXX: Python < 2.7 and < 3.2
    schema.complexTypes.sort(**kw)


def schema_to_py(schema, known_paths=None, known_types=None, location=None,
                 parent_namespace=None, base_path=None,
                 standalone=False, resolver=None):
    if base_path:
        rewrite_paths(schema, base_path)

    _reorder_complexTypes(schema)

    if known_paths is None:
        known_paths = []
    if location:
        known_paths.append(location)

    if schema.targetNamespace is None:
        schema.targetNamespace = parent_namespace
    if resolver is None:
        resolver = xsdresolve.XSDCachedSchemaResolver.create(base_path)

    if known_types is None:
        known_types = []

    env = get_rendering_environment(module='soapfish.xsd2py')
    env.globals.update(
        known_paths=known_paths,
        known_types=known_types,
        location=location,
        resolve_import=resolve_import,
        resolver=resolver,
    )
    if not standalone:
        del env.globals['preamble']
    tpl = env.get_template('xsd')

    return tpl.render(schema=schema, base_path=base_path)


# --- Program -----------------------------------------------------------------


def main(argv=None):
    stdin = getattr(sys.stdin, 'buffer', sys.stdin)
    stdout = getattr(sys.stdout, 'buffer', sys.stdout)

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Generates Python code from an XSD document.',
    )
    parser.add_argument('xsd', help='Input path to an XSD document.')
    parser.add_argument('output', help='Output path for Python code.', nargs='?',
                        type=argparse.FileType('wb'), default=stdout)
    opt = parser.parse_args(sys.argv[1:] if argv is None else argv)

    logger.info('Generating code for XSD document: %s' % opt.xsd)

    resolver = xsdresolve.XSDCachedSchemaResolver.create()
    if opt.xsd == '-':
        code = generate_code_from_xsd(stdin.read(), resolver=resolver, encoding='utf-8')
    else:
        code = generate_code_from_xsd_file(opt.xsd, resolver=resolver, encoding='utf-8')

    opt.output.write(code.strip())

    return 0


if __name__ == '__main__':

    sys.exit(main())

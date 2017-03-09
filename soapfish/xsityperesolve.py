import itertools

from . import utils


class XSITypeResolver(object):
    def __init__(self, schemas=[]):
        """
        Initializes the XSITypeResolver with schemas from which the types shall be resolved.
        :param schemas: a list of xsd.Schema instances
        :return:
        """
        self.schemas = schemas
        self.namespaces = None

    def resolvable_namespaces(self):
        """
        Gets namespaces from which this instance can resolve types.
        :return: a set of resolvable namespaces
        """
        if self.namespaces is None:
            def get_target_namespace(schema):
                return schema.targetNamespace

            def get_nested_schemas(schema):
                return list(itertools.chain(schema.imports, schema.includes))

            namespaces = set()
            schemas = self.schemas[:]
            while schemas:
                namespaces.update(map(get_target_namespace, schemas))
                schemas = sum(map(get_nested_schemas, schemas), [])
            self.namespaces = namespaces
        return self.namespaces

    def find_type(self, qname):
        """
        Finds class representing the specified type identified by its name.

        :param qname: type's QNAME as parsed from xsi:type attribute
        :return:
        """
        for schema in self.schemas:
            qname_cls = self._find_type_in_schema(schema, qname)
            if qname_cls is not None:
                return qname_cls
        else:
            return None

    @classmethod
    def _find_type_in_schema(cls, schema, qname):
        if qname.namespace == schema.targetNamespace:
            for t in itertools.chain(schema.complexTypes, schema.simpleTypes):
                if cls._get_type_localname(t) == qname.localname:
                    return t
        for nested_schema in itertools.chain(schema.imports, schema.includes):
            t = cls._find_type_in_schema(nested_schema, qname)
            if t is not None:
                return t
        return None

    @staticmethod
    def _get_type_localname(t):
        if t.XSI_TYPE:
            return t.XSI_TYPE.localname
        else:
            return utils.uncapitalize(t.__name__)

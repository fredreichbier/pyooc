import os

try:
    import simplejson as json
except ImportError:
    import json

class ModuleNotFound(Exception):
    pass

class Entity(object):
    def __init__(self, parent):
        self.parent = parent

class PropertyData(object):
    def __init__(self):
        self.has_getter = False
        self.has_setter = False
        self.full_getter_name = None
        self.full_setter_name = None

    def read(self, data):
        self.has_getter = data['hasGetter']
        self.has_setter = data['hasSetter']
        self.full_getter_name = data['fullGetterName']
        self.full_setter_name = data['fullSetterName']

class InterfaceImpl(Entity):
    def __init__(self, parent):
        Entity.__init__(self, parent)
        self.parent = parent
        self.for_ = None
        self.interface = None

    def read(self, data):
        self.for_ = data['for']
        self.interface = data['interface']

class GlobalVariable(Entity):
    def __init__(self, parent):
        Entity.__init__(self, parent)
        self.parent = parent
        self.name = None
        self.modifiers = None
        self.value = None
        self.type = None
        self.extern = None
        self.property_data = None

    def read(self, data):
        self.name = data['name']
        self.modifiers = data['modifiers']
        self.value = data['value']
        self.type = data['varType']
        self.extern = data['extern']
        if data['propertyData']:
            self.property_data = PropertyData()
            self.properts_data.read(data['propertyData'])

class Field(GlobalVariable):
    pass

class Classlike(Entity):
    def __init__(self, parent):
        Entity.__init__(self, parent)
        self.members = {}

    def read_members(self, members):
        dispatch = {
            'method': self.read_method,
            'field': self.read_field,
        }
        for entry in members:
            # TODO: PLEASE add versions support.
            name, entity = entry[:2]
            dispatch[entity['type']](entity)

    def read_method(self, entity):
        obj = Method(self)
        obj.read(entity)
        self.members[obj.name] = obj

    def read_field(self, entity):
        obj = Field(self)
        obj.read(entity)
        self.members[obj.name] = obj

class Class(Classlike):
    def __init__(self, parent):
        Classlike.__init__(self, parent)
        # to be set in `read`.
        self.name = None
        self.tag = None
        self.full_name = None

    def read(self, data):
        self.name = data['name']
        self.tag = data['tag']
        self.full_name = data['fullName']
        self.generic_types = data['genericTypes']
        self.extends = data['extends']
        self.abstract = data['abstract']
        self.doc = data['doc']
        self.read_members(data['members'])

class Cover(Classlike):
    def __init__(self, parent):
        Classlike.__init__(self, parent)
        # to be set in `read`.
        self.name = None
        self.tag = None
        self.from_ = None
        self.extends = None
        self.full_name = None

    def read(self, data):
        self.name = data['name']
        self.tag = data['tag']
        self.full_name = data['fullName']
        self.extends = data['extends']
        self.from_ = data['from']
        self.doc = data['doc']
        self.read_members(data['members'])

class Argument(object):
    def __init__(self, name, tag, modifiers=None):
        self.name = name
        self.tag = tag
        # store modifiers as list, even if they can be null in the json spec
        if modifiers is None:
            modifiers = []
        self.modifiers = modifiers

    @property
    def vararg(self):
        return self.name == '...'

class Function(Entity):
    def __init__(self, parent):
        Entity.__init__(self, parent)
        # to be set in `read`
        self.name = None
        self.tag = None
        self.modifiers = None
        self.generic_types = None
        self.extern = None
        self.return_type = None
        self.arguments = None

    @property
    def vararg(self):
        return self.arguments and self.arguments[-1].vararg

    def read(self, entity):
        self.name = entity['name']
        self.tag = entity['tag']
        self.modifiers = entity['modifiers']
        self.generic_types = entity['genericTypes']
        self.extern = entity['extern']
        self.return_type = entity['returnType']
        self.arguments = []
        for argobj in entity['arguments']:
            arg = Argument(*argobj)
            self.arguments.append(arg)

class Method(Function):
    pass

class Operator(Entity):
    def __init__(self, parent):
        Entity.__init__(self, parent)
        self.symbol = None
        self.name = None
        self.function = None
        self.tag = None

    def read(self, data):
        self.name = data['name']
        self.symbol = data['symbol']
        self.function = Function(self)
        self.function.read(data['function'])
        self.tag = data['tag']

class Interface(Classlike):
    def __init__(self, parent):
        Classlike.__init__(self, parent)
        self.name = None

    def read(self, data):
        self.name = data['name']
        self.read_members(data['members'])

class Module(Entity):
    def __init__(self):
        Entity.__init__(self, None)
        self.members = {}
        self.operators = set()
        self.interface_impls = set()
        self.path = None
        self.global_imports = None
        self.namespaced_imports = None
        self.uses = None

    def read(self, entity):
        # read the global information
        self.path = entity['path']
        self.global_imports = entity['globalImports']
        self.namespaced_imports = entity['namespacedImports']
        self.uses = entity['uses']
        # read the members
        dispatch = {
            'function': self.read_function,
            'class': self.read_class,
            'cover': self.read_cover,
            'globalVariable': self.read_global_variable,
            'operator': self.read_operator,
            'interface': self.read_interface,
            'interfaceImpl': self.read_interface_impl,
        }
        for entry in entity['entities']:
            # TODO: version support
            tag, entity = entry[:2]
            type = entity['type']
            dispatch[type](entity)

    def read_function(self, entity):
        obj = Function(self)
        obj.read(entity)
        self.members[obj.name] = obj

    def read_operator(self, entity):
        obj = Operator(self)
        obj.read(entity)
        self.operators.add(obj)

    def read_class(self, entity):
        obj = Class(self)
        obj.read(entity)
        self.members[obj.name] = obj

    def read_interface(self, entity):
        obj = Interface(self)
        obj.read(entity)
        self.members[obj.name] = obj

    def read_interface_impl(self, entity):
        obj = InterfaceImpl(self)
        obj.read(entity)
        self.interface_impls.add(obj)

    def read_cover(self, entity):
        obj = Cover(self)
        obj.read(entity)
        self.members[obj.name] = obj

    def read_global_variable(self, entity):
        obj = GlobalVariable(self)
        obj.read(entity)
        self.members[obj.name] = obj

class Repository(object):
    """
        A repository is a directory full of `.json` files. It's
        the output directory of a `ooc -backend=json` run.
    """
    def __init__(self, path):
        self.path = path
        self._modules_cache = {}

    def get_module(self, module):
        """
            Get the `Module` instance specified by the ooc module path *module*.
            Use the module cache.
        """
        if module not in self._modules_cache:
            self._modules_cache[module] = self._load_module(module)
        return self._modules_cache[module]

    def get_all_paths(self):
        """
            Get all possible module paths.
        """
        paths = []
        for dirpath, dirnames, filenames in os.walk(self.path):
            splitted = os.path.relpath(dirpath, self.path).split(os.path.sep)
            if len(splitted) > 2:
                package = '/'.join(splitted[2:])
            else:
                package = '/'.join(splitted[1:])
            for filename in filenames:
                if filename.endswith('.json'):
                    if package:
                        paths.append(package + '/' + os.path.splitext(filename)[0])
                    else:
                        paths.append(os.path.splitext(filename)[0])
        return paths

    def get_all_modules(self):
        """
            Get all possible modules as a dictionary mapping module paths to module instances.
        """
        return dict((path, self.get_module(path)) for path in self.get_all_paths())

    def _load_module(self, module):
        """
            Load the `Module` instance specified by the ooc module path *module*
            and return it.
        """
        filename = self.get_module_filename(module)
        with open(filename, 'r') as f:
            data = json.load(f)
        entity = Module()
        entity.read(data)
        return entity

    def get_module_filename(self, module):
        """
            Get the filename of the module description for *module*.
            *module* is an ooc-compliant module path (like "text/StringTokenizer",
            which will be translated to the filename "text/StringTokenizer.json").
            If the module is not found, `ModuleNotFound` is thrown.
        """
        parts = module.split('/')
        parts[-1] += '.json'
        filename = os.path.join(*parts)
        # Search for the constructed filename in all subdirectories of `self.path` (depth 2)
        for packagedir in os.listdir(self.path):
            packagedir = os.path.join(self.path, packagedir)
            for subdir in [''] + os.listdir(packagedir):
                subfilename = os.path.join(packagedir, subdir, filename)
                if os.path.isfile(subfilename):
                    return subfilename
        raise ModuleNotFound(module)


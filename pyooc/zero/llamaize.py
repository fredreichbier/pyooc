import ctypes

import pyooc.ffi as ffi
import pyooc.zero as zero
from pyooc.zero.tag import parse_string as parse_tag

class SorryError(NotImplementedError):
    pass

C_TYPES_MAP = {
    'int': ctypes.c_int,
    'va_list': ctypes.c_void_p,
}

def resolve_c_type(library, repo, zero_module, typename):
    if typename.endswith('*'):
        return ctypes.POINTER(resolve_c_type(library, repo, zero_module, typename[:-1]))
    return C_TYPES_MAP.get(typename, ctypes.c_void_p) # TODO: In doubt, just return c_void_p. That doesn't sound sane.

def resolve_type(library, repo, zero_module, tag):
    if '(' in tag:
        # has modifiers.
        mod, args = parse_tag(tag)
        if mod in ('pointer', 'reference'):
            # pointer and reference have the same handling
            return ctypes.POINTER(resolve_type(module, args[0]))
        else:
            raise SorryError('Unknown tag: %r' % tag)
    else:
        # just a name.
        module = library.get_module(zero_module.path)
        # search in current module
        if hasattr(module, tag):
            # yay!
            return getattr(module, tag)
        else:
            # nay.
            print 'searching in global imports - %r' % tag
            # TODO: namespaced imports
            for import_path in zero_module.global_imports:
                if hasattr(library.get_module(import_path), tag):
                    return getattr(library.get_module(import_path), tag)
            raise SorryError('Unknown type: %r' % tag)

def llamaize_function(library, repo, zero_module, cls_entity, entity):
    # arguments.
    arguments = []
    for arg in entity.arguments:
        if (arg.tag in entity.generic_types or arg.tag in cls_entity.generic_types):
            # generic.
            arguments.append(arg.tag)
        else:
            arguments.append(resolve_type(library, repo, zero_module, arg.tag))
    # return type.
    if entity.return_type is None:
        return_type = None
    elif (entity.return_type in entity.generic_types or entity.return_type in cls_entity.generic_types):
        return_type = entity.return_type
    else:
        return_type = resolve_type(library, repo, zero_module, entity.return_type)
    # modifiers.
    # well, i think only `static` has any effect here. right?
    static = 'extern' in entity.modifiers
    return {
        'name': entity.name,
        'arguments': arguments,
        'generic_types': entity.generic_types,
        'return_type': return_type,
        'generic_return_type': isinstance(return_type, basestring),
        'static': static,
    }

def llamaize_class(library, repo, zero_module, entity):
    """
        Return a :class:`pyooc.ffi.Class`.
    """
    methods = []
    fields = []
    static_methods = []
    generic_methods = []
    constructors = []
    for name, member in entity.members.iteritems():
        if isinstance(member, zero.Method):
            # Yay method! llamaize it ...
            llamaized = llamaize_function(library, repo, zero_module, entity, member)
            name = name.replace('~', '_')
            if name == 'init' or name.startswith('init~'):
                if '~' in name:
                    constructors.append((name[name.index('~') + 1:], llamaized['arguments']))
                else:
                    constructors.append(('', llamaized['arguments']))
            else:
                info = (name, llamaized['return_type'], llamaized['arguments'])
                if (llamaized['generic_types'] or llamaized['generic_return_type']):
                    if llamaized['static']:
                        raise SorryError('sorry, no static generic methods yet. here is your crowbar')
                    generic_methods.append((name, llamaized['generic_types'], llamaized['return_type'], llamaized['arguments']))
                    print generic_methods
                else:
                    if llamaized['static']:
                        static_methods.append(info)
                    else:
                        methods.append(info)
        else:
            print 'ignored', member

    dct = {
        '_name_': entity.name,
        '_fields_': fields,
        '_methods_': methods,
        '_static_methods_': static_methods,
        '_generic_methods_': generic_methods,
        '_constructors_': constructors,
        '_generic_types_': entity.generic_types, # isn't needed in Class, but we do it anyway.
    }
    module = library.get_module(zero_module.path)
    cls = getattr(module, entity.name)
    for n, i in dct.iteritems():
        setattr(cls, n, i)
    cls.bind(module)

def llamaize_class_minimal(library, repo, zero_module, entity):
    if entity.generic_types:
        cls = type(entity.name, (ffi.GenericClass,), {})
    else:
        cls = type(entity.name, (ffi.Class,), {})
    setattr(library.get_module(zero_module.path), entity.name, cls)

def llamaize_cover_minimal(library, repo, zero_module, entity):
    if entity.from_:
        fromtype = resolve_c_type(library, repo, zero_module, entity.from_)
        cls = type(entity.name, (fromtype, ffi.Cover), {})
    else:
        cls = type(entity.name, (ffi.Cover,), {})
    setattr(library.get_module(zero_module.path), entity.name, cls)

def llamaize_module(library, repo, path):
    """
        Return a :class:`pyooc.ffi.Module`.
    """
    # Do all deps minimally
    entity = repo.get_module(path)
    for import_path in entity.global_imports + ['lang/types']: # TODO: why do we have to add lang/types here?
        llamaize_module_minimal(library, repo, import_path)
    # Now do the real stuff.
    module = library.get_module(path)
    for name, member in entity.members.iteritems():
        if isinstance(member, zero.Class):
            llamaize_class(library, repo, entity, member)

def llamaize_module_minimal(library, repo, path):
    entity = repo.get_module(path)
    module = library.get_module(path)
    for name, member in entity.members.iteritems():
        if isinstance(member, zero.Class):
            llamaize_class_minimal(library, repo, entity, member)
        elif isinstance(member, zero.Cover):
            llamaize_cover_minimal(library, repo, entity, member)


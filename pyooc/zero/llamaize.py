import ctypes

import pyooc.ffi as ffi
import pyooc.zero as zero
from pyooc.zero.tag import parse_string as parse_tag

class SorryError(NotImplementedError):
    pass

C_TYPES_MAP = {
    'int': ctypes.c_int,
    'va_list': ctypes.c_void_p,
    'float': ctypes.c_float,
    'uint8_t': ctypes.c_uint8,
    'uint16_t': ctypes.c_uint16,
    'uint32_t': ctypes.c_uint32,
    'uint64_t': ctypes.c_uint64,
    'int8_t': ctypes.c_int8,
    'int16_t': ctypes.c_int16,
    'int32_t': ctypes.c_int32,
    'int64_t': ctypes.c_int64,
    'signed long': ctypes.c_long,
    'unsigned long': ctypes.c_ulong,
    'bool': ctypes.c_bool,
    'long double': ctypes.c_longdouble,
    'wchar_t': ctypes.c_wchar,
    'size_t': ctypes.c_size_t,
    'double': ctypes.c_double,
    'unsigned long long': ctypes.c_ulonglong,
    'char': ctypes.c_char,
    'double': ctypes.c_double,
    'unsigned char': ctypes.c_ubyte,
    'void*': ctypes.c_void_p,
    'signed short': ctypes.c_short,
    'unsigned short': ctypes.c_ushort,
    'signed long long': ctypes.c_longlong,
    'signed int': ctypes.c_int,
    'unsigned int': ctypes.c_uint,
    'signed char': ctypes.c_char,
}

def resolve_c_type(library, repo, zero_module, typename):
    if typename in C_TYPES_MAP:
        return C_TYPES_MAP[typename]
    elif typename.endswith('*'):
        return ctypes.POINTER(resolve_c_type(library, repo, zero_module, typename[:-1]))
    else:
        print 'Unknown type: %r' % typename
        return ctypes.c_void_p

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
            # TODO: namespaced imports
            # types?
            for import_path in zero_module.global_imports:
                if hasattr(library.get_module(import_path), tag):
                    return getattr(library.get_module(import_path), tag)
            if hasattr(library.types, tag):
                return getattr(library.types, tag)
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
        Works for classes and covers!
    """
    methods = []
    static_methods = []
    generic_methods = []
    fields = []
    static_fields = []
    constructors = []
    for name, member in entity.members.iteritems():
        if isinstance(member, zero.Method):
            # Yay method! llamaize it ...
            llamaized = llamaize_function(library, repo, zero_module, entity, member)
            if name in ('new', 'init') or name.startswith('new~') or name.startswith('init~'):
                if '~' in name:
                    cname = name[name.index('~') + 1:]
                else:
                    cname = ''
                if not any(t[0] == cname for t in constructors):
                    constructors.append((cname, llamaized['arguments']))
            else:
                name = name.replace('~', '_')
                info = (name, llamaized['return_type'], llamaized['arguments'])
                if (llamaized['generic_types'] or llamaized['generic_return_type']):
                    if llamaized['static']:
                        raise SorryError('sorry, no static generic methods yet. here is your crowbar')
                    generic_methods.append((name, llamaized['generic_types'], llamaized['return_type'], llamaized['arguments']))
                else:
                    if llamaized['static']:
                        static_methods.append(info)
                    else:
                        methods.append(info)
        elif isinstance(member, zero.Field):
            if member.type in entity.generic_types:
                var_type = member.type
            else:
                var_type = resolve_type(library, repo, zero_module, member.type)
            if member.name in entity.generic_types:
                # skip the T/U/V... members, they're added in _setup
                continue
            field = (member.name, var_type)
            if 'static' in member.modifiers:
                static_fields.append(field)
            else:
                fields.append(field)
        else:
            print 'ignored', member
    super_class = resolve_type(library, repo, zero_module, entity.extends)
    # Finally, create the class.
    dct = {
        '_name_': entity.name,
        '_fields_': fields,
        '_static_fields_': static_fields,
        '_methods_': methods,
        '_extends_': super_class,
        '_static_methods_': static_methods,
        '_generic_methods_': generic_methods,
        '_constructors_': constructors,
        '_generic_types_': getattr(entity, 'generic_types', None), # isn't needed in Class/Cover, but we do it anyway.
    }
    module = library.get_module(zero_module.path)
    cls = getattr(module, entity.name)
    for n, i in dct.iteritems():
        setattr(cls, n, i)
    cls.bind(module)

def llamaize_class_minimal(library, repo, zero_module, entity):
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
    if path == 'lang/types':
        return
    # Do all deps minimally
    entity = repo.get_module(path)
    for import_path in entity.global_imports:
        llamaize_module_minimal(library, repo, import_path)
    # Do myself minimally.
    llamaize_module_minimal(library, repo, path)
    # Now do the real stuff.
    module = library.get_module(path)
    for name, member in entity.members.iteritems():
        if isinstance(member, (zero.Class, zero.Cover)):
            llamaize_class(library, repo, entity, member)

def llamaize_module_minimal(library, repo, path):
    if path == 'lang/types':
        return
    entity = repo.get_module(path)
    module = library.get_module(path)
    for name, member in entity.members.iteritems():
        if isinstance(member, zero.Class):
            llamaize_class_minimal(library, repo, entity, member)
        elif isinstance(member, zero.Cover):
            llamaize_cover_minimal(library, repo, entity, member)


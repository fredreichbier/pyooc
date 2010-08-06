import ctypes

import pyooc.ffi as ffi
import pyooc.parser as parser
from pyooc.parser.tag import parse_string as parse_tag

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

def resolve_c_type(library, repo, parser_module, typename):
    if typename in C_TYPES_MAP:
        return C_TYPES_MAP[typename]
    elif typename.endswith('*'):
        return ctypes.POINTER(resolve_c_type(library, repo, parser_module, typename[:-1]))
    else:
        # maybe it's a ooc type.
        try:
            return resolve_type(library, repo, parser_module, typename)
        except SorryError:
            print 'Unknown type: %r' % typename
            return ctypes.c_void_p

def resolve_type(library, repo, parser_module, tag):
    if '(' in tag:
        # has modifiers.
        mod, args = parse_tag(tag)
        if mod in ('pointer', 'reference'):
            # pointer and reference have the same handling
            return ctypes.POINTER(resolve_type(library, repo, parser_module, args[0]))
        else:
            raise SorryError('Unknown tag: %r' % tag)
    else:
        # just a name.
        module = library.get_module(parser_module.path)
        # search in current module
        if hasattr(module, tag):
            # yay!
            return getattr(module, tag)
        else:
            # nay.
            # types? Since lang/* modules are imported automatically anyway,
            # it's no problem to look through them before looking through
            # explicitly imported modules. Right? (TODO)
            # The other way round, it will cause problems because we'd have
            # `String` defined multiple times. TODO anyway.
            if hasattr(library.types, tag):
                return getattr(library.types, tag)
            # TODO: namespaced imports
            for import_path in parser_module.global_imports:
                if hasattr(library.get_module(import_path), tag):
                    return getattr(library.get_module(import_path), tag)
            raise SorryError('Unknown type: %r' % tag)

def bind_function(library, repo, parser_module, cls_entity, entity):
    # arguments.
    arguments = []
    for arg in entity.arguments:
        if (arg.tag in entity.generic_types or arg.tag in cls_entity.generic_types):
            # generic.
            arguments.append(arg.tag)
        else:
            arguments.append(resolve_type(library, repo, parser_module, arg.tag))
    # return type.
    if entity.return_type is None:
        return_type = None
    elif entity.return_type.startswith('multi('):
        # multi-return ...
        return_type = []
        for rtype in parse_tag(entity.return_type)[1]:
            if (rtype in entity.generic_types or rtype in cls_entity.generic_types):
                return_type.append(rtype)
            else:
                return_type.append(resolve_type(library, repo, parser_module, rtype))
        return_type = tuple(return_type)
    elif (entity.return_type in entity.generic_types or entity.return_type in cls_entity.generic_types):
        return_type = entity.return_type
    else:
        return_type = resolve_type(library, repo, parser_module, entity.return_type)
    # modifiers.
    # well, i think only `static` has any effect here. right?
    static = 'static' in entity.modifiers
    return {
        'name': entity.name,
        'arguments': arguments,
        'generic_types': entity.generic_types,
        'return_type': return_type,
        'generic_return_type': isinstance(return_type, basestring),
        'static': static,
    }

def bind_class(library, repo, parser_module, entity):
    """
        Works for classes and covers!
    """
    funcs = []
    fields = []
    static_fields = []
    for name, member in entity.members.iteritems():
        if isinstance(member, parser.Method):
            # Yay method! bind it ...
            bindd = bind_function(library, repo, parser_module, entity, member)
            if (bindd['generic_types'] or bindd['generic_return_type']):
                if bindd['static']:
                    print '%r: sorry, no static generic methods yet. here is your crowbar' % bindd['name']
                funcs.append(ffi.Func(name,
                    generictypes=bindd['generic_types'],
                    restype=bindd['return_type'],
                    argtypes=bindd['arguments'],
                    overrides=member.overrides))
            else:
                funcs.append(ffi.Func(name,
                restype=bindd['return_type'],
                argtypes=bindd['arguments'],
                static=bindd['static'],
                overrides=member.overrides))
        elif isinstance(member, parser.Field):
            if member.type in entity.generic_types:
                var_type = member.type
            else:
                var_type = resolve_type(library, repo, parser_module, member.type)
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
    super_class = resolve_type(library, repo, parser_module, entity.extends)
    # Finally, create the class.
    dct = {
        '_name_': entity.name,
        '_fields_': fields,
        '_static_fields_': static_fields,
        '_methods_': funcs,
        '_extends_': super_class,
        '_generictypes_': getattr(entity, 'generic_types', None), # isn't needed in Class/Cover, but we do it anyway.
    }
    module = library.get_module(parser_module.path)
    cls = getattr(module, entity.name)
    for n, i in dct.iteritems():
        setattr(cls, n, i)
    cls.bind(module)

def bind_class_minimal(library, repo, parser_module, entity):
    cls = type(entity.name, (ffi.Class,), {})
    setattr(library.get_module(parser_module.path), entity.name, cls)

def bind_cover_minimal(library, repo, parser_module, entity):
    if entity.from_:
        fromtype = resolve_c_type(library, repo, parser_module, entity.from_)
        cls = type(entity.name, (fromtype, ffi.Cover), {})
    else:
        cls = type(entity.name, (ffi.Cover,), {})
    setattr(library.get_module(parser_module.path), entity.name, cls)

def bind_module(library, repo, path):
    """
        Return a :class:`pyooc.ffi.Module`.
    """
    if path == 'lang/types':
        return
    # Do all deps minimally
    entity = repo.get_module(path)
    for import_path in entity.global_imports:
        bind_module_minimal(library, repo, import_path)
    # Do myself minimally.
    bind_module_minimal(library, repo, path)
    # Now do the real stuff.
    module = library.get_module(path)
    for name, member in entity.members.iteritems():
        if isinstance(member, (parser.Class, parser.Cover)):
            bind_class(library, repo, entity, member)

def bind_module_minimal(library, repo, path):
    if path == 'lang/types':
        return
    entity = repo.get_module(path)
    module = library.get_module(path)
    for name, member in entity.members.iteritems():
        if isinstance(member, parser.Class):
            bind_class_minimal(library, repo, entity, member)
        elif isinstance(member, parser.Cover):
            bind_cover_minimal(library, repo, entity, member)


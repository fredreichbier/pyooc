import os
import tempfile
import shutil
from subprocess import Popen, PIPE

from pyooc.ffi import Library
from pyooc.parser import Repository
from pyooc.bind import bind_module

class CompileError(Exception):
    pass

def compile_and_bind(sourcecode, compiler='rock'):
    # Create temporary files for the sourcecode ...
    source_fd, source_filename = tempfile.mkstemp('.ooc')
    source_dirname, source_basename = os.path.split(source_filename)
    modulename = os.path.splitext(source_basename)[0]
    os.close(source_fd)
    # ... and the library. TODO: Other platforms!
    lib_fd, lib_filename = tempfile.mkstemp('.so')
    soname = os.path.splitext(os.path.basename(lib_filename))[0]
    os.close(lib_fd)
    # And a temporary directory for the json repository.
    repo_dir = tempfile.mkdtemp('.repo')
    # Write the sourcecode.
    with open(source_filename, 'w') as f:
        f.write(sourcecode)
    try:
        # Compile it.
        proc = Popen([
                    compiler,
                    '-nolibcache',
                    '-o=%s' % lib_filename,
                    '-noclean',
                    '-g',
                    '+-shared',
                    '+-fPIC',
                    '+-Wl,-export-dynamic,-soname,%s' % soname,
                    source_basename],
                    cwd=source_dirname, # TODO: rock absolute path bug workaround
                    stdout=PIPE,
                    stderr=PIPE)
        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            raise CompileError('Compile fail! stdout=%s, stderr=%s' % (stdout, stderr))
        # Create the repository, invoke the JSON backend.
        proc = Popen([
                    compiler,
                    '-backend=json',
                    '-outpath=%s' % repo_dir,
                    source_basename],
                    cwd=source_dirname, # TODO: see above
                    stdout=PIPE,
                    stderr=PIPE)
        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            raise CompileError('JSON backend fail! stdout=%s, stderr=%s' % (stdout, stderr))
        # Yay! Lib! Repo!
        lib = Library(lib_filename)
        repo = Repository(repo_dir)
        # Biiiiind.
        bind_module(lib, repo, modulename)
        return lib.get_module(modulename)
    finally:
        # Cleanup.
        os.remove(source_filename)
        os.remove(lib_filename) # TODO: <- That's okay, isn't it?
        shutil.rmtree(repo_dir)

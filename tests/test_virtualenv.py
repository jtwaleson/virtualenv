import virtualenv
import optparse
import os
import shutil
import sys
import tempfile
from mock import patch, Mock


def test_version():
    """Should have a version string"""
    assert virtualenv.virtualenv_version, "Should have version"


@patch('os.path.exists')
def test_resolve_interpreter_with_absolute_path(mock_exists):
    """Should return absolute path if given and exists"""
    mock_exists.return_value = True
    virtualenv.is_executable = Mock(return_value=True)

    exe = virtualenv.resolve_interpreter("/usr/bin/python42")

    assert exe == "/usr/bin/python42", "Absolute path should return as is"
    mock_exists.assert_called_with("/usr/bin/python42")
    virtualenv.is_executable.assert_called_with("/usr/bin/python42")


@patch('os.path.exists')
def test_resolve_interpreter_with_nonexistent_interpreter(mock_exists):
    """Should exit when with absolute path if not exists"""
    mock_exists.return_value = False

    try:
        virtualenv.resolve_interpreter("/usr/bin/python42")
        assert False, "Should raise exception"
    except SystemExit:
        pass

    mock_exists.assert_called_with("/usr/bin/python42")


@patch('os.path.exists')
def test_resolve_interpreter_with_invalid_interpreter(mock_exists):
    """Should exit when with absolute path if not exists"""
    mock_exists.return_value = True
    virtualenv.is_executable = Mock(return_value=False)

    try:
        virtualenv.resolve_interpreter("/usr/bin/python42")
        assert False, "Should raise exception"
    except SystemExit:
        pass

    mock_exists.assert_called_with("/usr/bin/python42")
    virtualenv.is_executable.assert_called_with("/usr/bin/python42")


def test_activate_after_future_statements():
    """Should insert activation line after last future statement"""
    script = [
        '#!/usr/bin/env python',
        'from __future__ import with_statement',
        'from __future__ import print_function',
        'print("Hello, world!")'
    ]
    assert virtualenv.relative_script(script) == [
        '#!/usr/bin/env python',
        'from __future__ import with_statement',
        'from __future__ import print_function',
        '',
        "import os; activate_this=os.path.join(os.path.dirname(os.path.realpath(__file__)), 'activate_this.py'); execfile(activate_this, dict(__file__=activate_this)); del os, activate_this",
        '',
        'print("Hello, world!")'
    ]


def test_cop_update_defaults_with_store_false():
    """store_false options need reverted logic"""
    class MyConfigOptionParser(virtualenv.ConfigOptionParser):
        def __init__(self, *args, **kwargs):
            self.config = virtualenv.ConfigParser.RawConfigParser()
            self.files = []
            optparse.OptionParser.__init__(self, *args, **kwargs)

        def get_environ_vars(self, prefix='VIRTUALENV_'):
            yield ("no_site_packages", "1")

    cop = MyConfigOptionParser()
    cop.add_option(
        '--no-site-packages',
        dest='system_site_packages',
        action='store_false',
        help="Don't give access to the global site-packages dir to the "
             "virtual environment (default)")

    defaults = {}
    cop.update_defaults(defaults)
    assert defaults == {'system_site_packages': 0}

def test_install_python_bin():
    """Should create the right python executables and links"""
    tmp_virtualenv = tempfile.mkdtemp()
    try:
        home_dir, lib_dir, inc_dir, bin_dir = \
                                virtualenv.path_locations(tmp_virtualenv)
        virtualenv.install_python(home_dir, lib_dir, inc_dir, bin_dir, False,
                                  False)

        if virtualenv.is_win:
            required_executables = [ 'python.exe', 'pythonw.exe']
        else:
            py_exe_no_version = 'python'
            py_exe_version_major = 'python%s' % sys.version_info[0]
            py_exe_version_major_minor = 'python%s.%s' % (
                sys.version_info[0], sys.version_info[1])
            required_executables = [ py_exe_no_version, py_exe_version_major,
                                     py_exe_version_major_minor ]

        for pth in required_executables:
            assert os.path.exists(os.path.join(bin_dir, pth)), ("%s should "
                            "exist in bin_dir" % pth)
    finally:
        shutil.rmtree(tmp_virtualenv)

def test_64bit_technique():
    """
    Confirm the technique for determining 64bit in the embedded site.py
    is returning an expected answer
    """
    import struct
    assert (
        struct.calcsize("P") == 8 #64bit
        or
        struct.calcsize("P") == 4 #32bit
        )

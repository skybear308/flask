# -*- coding: utf-8 -*-
"""
    tests.conftest
    ~~~~~~~~~~~~~~

    :copyright: (c) 2014 by the Flask Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import pkgutil
import pytest
import sys
import textwrap


@pytest.fixture(params=(True, False))
def limit_loader(request, monkeypatch):
    """Patch pkgutil.get_loader to give loader without get_filename or archive.

    This provides for tests where a system has custom loaders, e.g. Google App
    Engine's HardenedModulesHook, which have neither the `get_filename` method
    nor the `archive` attribute.

    This fixture will run the testcase twice, once with and once without the
    limitation/mock.
    """
    if not request.param:
        return

    class LimitedLoader(object):
        def __init__(self, loader):
            self.loader = loader

        def __getattr__(self, name):
            if name in ('archive', 'get_filename'):
                msg = 'Mocking a loader which does not have `%s.`' % name
                raise AttributeError(msg)
            return getattr(self.loader, name)

    old_get_loader = pkgutil.get_loader

    def get_loader(*args, **kwargs):
        return LimitedLoader(old_get_loader(*args, **kwargs))
    monkeypatch.setattr(pkgutil, 'get_loader', get_loader)


@pytest.fixture
def apps_tmpdir(tmpdir, monkeypatch):
    '''Test folder for all instance tests.'''
    rv = tmpdir.mkdir('test_apps')
    monkeypatch.syspath_prepend(str(rv))
    return rv


@pytest.fixture
def apps_tmpdir_prefix(apps_tmpdir, monkeypatch):
    monkeypatch.setattr(sys, 'prefix', str(apps_tmpdir))
    return apps_tmpdir


@pytest.fixture
def site_packages(apps_tmpdir, monkeypatch):
    '''Create a fake site-packages'''
    rv = apps_tmpdir \
        .mkdir('lib')\
        .mkdir('python{x[0]}.{x[1]}'.format(x=sys.version_info))\
        .mkdir('site-packages')
    monkeypatch.syspath_prepend(str(rv))
    return rv


@pytest.fixture
def install_egg(apps_tmpdir, monkeypatch):
    '''Generate egg from package name inside base and put the egg into
    sys.path'''
    def inner(name, base=apps_tmpdir):
        if not isinstance(name, str):
            raise ValueError(name)
        base.join(name).ensure_dir()
        base.join(name).join('__init__.py').ensure()

        egg_setup = base.join('setup.py')
        egg_setup.write(textwrap.dedent("""
        from setuptools import setup
        setup(name='{0}',
              version='1.0',
              packages=['site_egg'],
              zip_safe=True)
        """.format(name)))

        import subprocess
        subprocess.check_call(
            [sys.executable, 'setup.py', 'bdist_egg'],
            cwd=str(apps_tmpdir)
        )
        egg_path, = apps_tmpdir.join('dist/').listdir()
        monkeypatch.syspath_prepend(str(egg_path))
        return egg_path
    return inner


@pytest.fixture
def purge_module(request):
    def inner(name):
        request.addfinalizer(lambda: sys.modules.pop(name, None))
    return inner

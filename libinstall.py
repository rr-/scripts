import shutil
import os
import sys
import subprocess

def run_silent(p):
    proc = subprocess.Popen(p, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    return (proc.returncode == 0, out, err)

def run_verbose(p):
    return subprocess.call(p) == 0

class FileInstaller(object):
    @staticmethod
    def confirm_executable(program):
        if not FileInstaller.has_executable(program):
            raise RuntimeError('%s not installed, cannot proceed' % program)

    @staticmethod
    def has_executable(program):
        return shutil.which(program) is not None

    @staticmethod
    def copy_file(source, target):
        source = os.path.abspath(os.path.expanduser(source))
        target = os.path.expanduser(target)
        if target.endswith('/') or target.endswith('\\'):
            target = os.path.join(target, os.path.basename(source))

        if os.path.islink(target):
            print('Removing old symlink...')
            os.unlink(target)

        print('Copying %s to %s...' % (source, target))
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copy(source, target)

    @staticmethod
    def create_symlink(source, target):
        source = os.path.abspath(os.path.expanduser(source))
        target = os.path.expanduser(target)
        if target.endswith('/') or target.endswith('\\'):
            target = os.path.join(target, os.path.basename(source))

        if os.path.islink(target):
            print('Removing old symlink...')
            os.unlink(target)
        elif os.path.exists(target):
            raise RuntimeError('Target file %s exists and is not a symlink.' % target)

        print('Linking %s to %s...' % (source, target))
        os.makedirs(os.path.dirname(target), exist_ok=True)
        os.symlink(source, target)

class CygwinPackageInstaller(object):
    name = 'cygwin'

    def supported(self):
        return FileInstaller.has_executable('apt-cyg')

    def is_installed(self, package):
        return len(run_silent(['apt-cyg', 'list', '^%s$' % package])[1]) > 0

    def is_available(self, package):
        return len(run_silent(['apt-cyg', 'listall', '^%s$' % package])[1]) > 0

    def install(self, package):
        return run_verbose(['apt-cyg', 'install', package])

class PacmanPackageInstaller(object):
    name = 'pacman'

    def supported(self):
        return FileInstaller.has_executable('pacman') and FileInstaller.has_executable('sudo')

    def is_installed(self, package):
        return run_silent(['pacman', '-Q', package])[0]

    def is_available(self, package):
        return run_silent(['pacman', '-Ss', package])[0]

    def install(self, package):
        return run_verbose(['sudo', 'pacman', '-S', package])

class PackageInstaller(object):
    INSTALLERS = {
        CygwinPackageInstaller(),
        PacmanPackageInstaller(),
    }

    @staticmethod
    def try_install(package, method=None):
        try:
            PackageInstaller.install(package, method)
        except Exception as e:
            print('Error installing %s: %s' % (package, e))

    @staticmethod
    def install(package, method=None):
        if method is None:
            chosen_installers = PackageInstaller.INSTALLERS
        else:
            chosen_installers = [i for i in PackageInstaller.INSTALLERS if i.name == method]

        chosen_installers = [i for i in chosen_installers if i.supported()]
        if len(chosen_installers) == 0:
            raise RuntimeError('No package manager is supported on this system!')

        for installer in chosen_installers:
            if installer.is_installed(package):
                print('Package %s is already installed.' % package)
                return True
            elif installer.is_available(package):
                print('Package %s is available, installing with %s' % (package, installer.name))
                return installer.install(package)

        raise RuntimeError('No package manager is capable of installing %s' % package)
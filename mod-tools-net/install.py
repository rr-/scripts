import sys
import packages
import util

packages.try_install('wget')
packages.try_install('curl')
if 'cygwin' in sys.platform:
    packages.try_install('ssh')
else:
    packages.try_install('openssh')

util.create_symlink('./ssh', '~/.ssh')
util.run_verbose(['chmod', '0600', util.abs_path('~/.ssh/config')])

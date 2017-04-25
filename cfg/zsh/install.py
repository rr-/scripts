from os.path import expanduser
from dotinstall import packages
from dotinstall import util


def run():
    packages.try_install('zsh')
    util.create_symlink('./zshrc', '~/.zshrc')
    util.create_dir('~/.config/zsh')

    util.run_verbose(['lesskey', '-o', expanduser('~/.less'), '--', './lesskey'])
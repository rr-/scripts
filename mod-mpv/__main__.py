#!/bin/python
import os
from libinstall import FileInstaller, PackageInstaller
dir = os.path.dirname(__file__)

PackageInstaller.try_install('luajit')
PackageInstaller.try_install('mpv-git')
FileInstaller.create_symlink(os.path.join(dir, 'config'), '~/.config/mpv')

import helpers.h
from os import walk

f = []
for (dirpath, dirnames, filenames) in walk(helpers.h.getScriptDir()):
	f.extend(filenames)
	break
__all__ = []
for file in f:
	if (file.endswith(".py")) and file != "__init__.py":
		__all__.append(file[:-3])  # remove extension

from . import *  # IMPORTANT!

#!/usr/bin/python

try:
	from lib.main import Main
except ImportError, err:
	from lib.core.core import Core
	Core.print_error(err)

##
### Main, go Galkan go go go ...
##

if __name__ == "__main__":

	flashlight = Main()
	flashlight._run(flashlight._args.scan_type)


#!/usr/bin/env python

from __future__ import print_function

__copyright__ = __license__ =  """
Copyright 2013-2016 Adobe Systems Incorporated. All rights reserved.

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

__doc__ = """
ufo2pfa v2.0 - Feb 03 2016

This script takes a path to a folder as input, finds all the UFO fonts
inside that folder and its subdirectories, and converts them to Type 1
fonts (.pfa files). If a path is not provided, the script will use the
current path as the top-most directory.

==================================================
Versions:
v1.0 - Feb 23 2013 - Initial release
v2.0 - Feb 03 2016 - Modernized and removed defcon and ufo2fdk dependencies.
"""

import sys, os, time
from subprocess import Popen, PIPE


fontsList = []


def getFontPaths(path):
	for r,folders,files in os.walk(path):
		for folder in folders:
			if folder[-4:].lower() == ".ufo":
				fontsList.append(os.path.join(r, folder))


def doTask(fonts):
	totalFonts = len(fonts)
	print("%d fonts found" % totalFonts)
	i = 1

	for font in fonts:
		folderPath, fontFileName = os.path.split(font)  # path to the folder where the font is contained and the font's file name
		styleName = os.path.basename(folderPath) # name of the folder where the font is contained

		# Change current directory to the folder where the font is contained
		os.chdir(folderPath)

		print('\n*******************************')
		print('Processing %s...(%d/%d)' % (styleName, i, totalFonts))

		# Assemble PFA file name
		fileNameNoExtension, fileExtension = os.path.splitext(fontFileName)
		pfaPath = fileNameNoExtension + '.pfa'

		# Convert UFO to PFA using tx
		cmd = 'tx -t1 "%s" "%s"' % (fontFileName, pfaPath)
		popen = Popen(cmd, shell=True, stdout=PIPE)
		popenout, popenerr = popen.communicate()
		if popenout:
			print(popenout)
		if popenerr:
			print(popenerr)

		i += 1


def run():
	# if a path is provided
	if len(sys.argv[1:]):
		baseFolderPath = sys.argv[1]

		if baseFolderPath[-1] == '/':  # remove last slash if present
			baseFolderPath = baseFolderPath[:-1]

		# make sure the path is valid
		if not os.path.isdir(baseFolderPath):
			print('Invalid directory.')
			return

	# if a path is not provided, use the current directory
	else:
		baseFolderPath = os.getcwd()

	t1 = time.time()

	getFontPaths(os.path.abspath(baseFolderPath))

	if len(fontsList):
		doTask(fontsList)
	else:
		print("No fonts found.")
		return

	t2 = time.time()
	elapsedSeconds = t2-t1

	if (elapsedSeconds/60) < 1:
		print('\nCompleted in %.1f seconds.' % elapsedSeconds)
	else:
		print('\nCompleted in %.1f minutes.' % (elapsedSeconds/60))


if __name__=='__main__':
	run()

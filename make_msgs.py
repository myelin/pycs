#!/usr/bin/env python

import re
import glob

sres = [
	re.compile('_\((\"\"\".*?\"\"\")\)', re.DOTALL),
	re.compile("_\(('.*?')\)", re.DOTALL),
	re.compile('_\(("[^"].*?")\)', re.DOTALL)
]

liste = glob.glob('*.py')
liste.extend(glob.glob('*/*.py'))
liste.extend(glob.glob('*/*/*.py'))

for file in liste:
	f = open(file)
	txt = f.read()
	f.close()
	strings = []
	for sre in sres:
		strings.extend(sre.findall(txt))
	if strings:
		print '# strings from %s' % file
		for s in strings:
			try:
				s = repr(eval(s))
				print "%s:=%s" % (s, s)
			except:
				print "# unparseable: %s" % repr(s)
		print


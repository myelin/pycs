#!/usr/bin/env python

import re
import sys
import glob

lang = None
try:
	lang = sys.argv[1]
except:
	print "usage:"
	print "   python make_msgs.py <lang>|empty"
	sys.exit(1)

catalog = {}

if lang != 'empty':
	lf = open('pycs-%s.msgs' % lang)
	line = lf.readline()
	while line:
		line = line.strip()
		if line and line[0] != '#':
			p = line.find('::=')
			if p > 0:
				msg1 = line[:p]
				msg2 = line[p+3:]
				if msg2:
					catalog[msg1] = msg2
		line = lf.readline()
	lf.close()

sres = [
	re.compile('_\((\"\"\".*?\"\"\")\)', re.DOTALL),
	re.compile("_\(('.*?')\)", re.DOTALL),
	re.compile('_\(("[^"].*?")\)', re.DOTALL)
]

liste = glob.glob('*.py')
liste.extend(glob.glob('*/*.py'))
liste.extend(glob.glob('*/*/*.py'))
liste.sort()

strh = {}

for file in liste:
	f = open(file)
	txt = f.read()
	f.close()
	strings = []
	for sre in sres:
		strings.extend(sre.findall(txt))
	if strings:
		strlh = {}
		print '# strings from %s' % file
		for s in strings:
			try:
				ps = repr(eval(s))
			except:
				print "# unparseable: %s" % s
			if ps and not(strlh.has_key(ps)):
				if strh.has_key(ps):
					print "# already defined: %s" % s
				else:
					strh[ps] = 1
					strlh[ps] = 1
					s2 = repr(eval(catalog.get(ps, s)))
					print "%s::=%s" % (ps, s2)
		print


#!/usr/bin/python

# Python Community Server
#
#     pycs_translation.py: handle string translations
#
# Copyright (c) 2002, Georg Bauer <gb@murphy.bofh.ms>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all 
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR 
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER 
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import os
import sys
import gettext
import pycs_paths

# This class handles our own translation format

class PyCSTranslations(gettext.NullTranslations):

	def _parse(self, fp):
		self._catalog = catalog = {}
		self._failedlog = os.path.join(pycs_paths.LOGDIR, 'failedmsg.log')
		line = fp.readline()
		while line:
			line = line.strip()
			if line and line[0] != '#':
				p = line.find('::=')
				if p > 0:
					msg1 = line[:p]
					msg2 = line[p+3:]
					if msg2:
						catalog[msg1] = eval(msg2)
			line = fp.readline()

	def gettext(self, message):
		msg = repr(message)
		if self._catalog.has_key(msg):
			return self._catalog[msg]
		else:
			try:
				flog = open(self._failedlog, 'a')
				flog.write('%s::=%s\n' % (msg, msg))
				flog.close()
			except:
				print "Missing msg: %s" % msg
			return message

	def ugettext(self, message):
		tmsg = self.gettext(message)
		return unicode(tmsg, self._charset)

# return a translation object for a given language. If possible use
# PyCSTranslations, but if not possible fall back to NullTranslations.

def translation(language):
	msgs = os.path.join(pycs_paths.RODIR, 'messages', 'pycs-%s.msgs' % language)
	if os.path.exists(msgs):
		try:
			msgf = open(msgs)
			trns = PyCSTranslations(msgf)
			msgf.close()
			return trns
		except:
			print "No global translation for %s found" % language
			return gettext.NullTranslations()
	else:
		try:
			msgf = open('pycs-%s.msgs' % language)
			trns = PyCSTranslations(msgf)
			msgf.close()
			return trns
		except:
			print "No local translation for %s found" % language
			return gettext.NullTranslations()

if __name__ == '__main__':
	translation('de').install()
	print _('Hello World')
	print _('This is a test')


# Python Community Server
#
#     search_engines.py: List of search engines for modules
#
# Copyright (c) 2002, Georg Bauer <gb@muensterland.org>
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

import re

engines = {
	'google': [
		re.compile(r'^http://.*\.google\..*[\?&]q=([^&]*).*$'),
		re.compile(r'^http://.*\.google\..*[\?&]as_q=([^&]*).*$'),
		],
	'alltheweb': [
		re.compile(r'^http://.*\.alltheweb\..*[\?&]q=([^&]*).*$'),
		],
	'feedster': [
		re.compile(r'^http://.*\.feedster\..*[\?&]q=([^&]*).*$'),
		],
	'freshmeat': [
		re.compile(r'^http://freshmeat\..*[\?&]q=([^&]*).*$'),
		],
	'daypop': [
		re.compile(r'^http://.*\.daypop\..*[\?&]q=([^&]*).*$'),
		],
	'geourl': [
		re.compile(r'^http://geourl\..*[\?&]p=([^&]*).*$'),
		],
	'yahoo': [
		re.compile(r'^http://.*\.yahoo\..*[\?&]p=([^&]*).*$'),
		],
	'altavista': [
		re.compile(r'^http://.*\.altavista\..*[\?&]q=([^&]*).*$'),
		],
	'msn': [
		re.compile(r'^http://search\.msn\..*[\?&]q=([^&]*).*$'),
		],
	'blo.gs': [
		re.compile(r'^http://blo\.gs\/\?q=([^&]*).*$'),
		],
	'lycos': [
		re.compile(r'^http://.*\.lycos\..*[\?&]query=([^&]*).*$'),
		],
	'aol': [
		re.compile(r'^http://.*\.aol\..*search.jsp\?q=([^&]*).*$'),
		re.compile(r'^http://.*\.aol\..*[\?&]query=([^&]*).*$'),
		],
	't-online': [
		re.compile(r'^http://.*\.t-online\..*tsc\?q=([^&]*).*$'),
		],
	'Virgilio': [
		re.compile(r'^http://.*\.virgilio\..*search\.cgi\?qs=([^&]*).*$'),
		],
	'mysearch': [
		re.compile(r'^http://.*\.mysearch\..*[\?&]searchfor=([^&]*).*$'),
	],
	}

def checkUrlForSearchEngine(url):
	matched = None
	term = None
	for engine in engines.keys():
		for termre in engines[engine]:
			m = termre.match(url)
			if m:
				matched = engine
				term = m.group(1)
	return (matched, term)


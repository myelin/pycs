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
		re.compile(r'^http://.*google\..*[\?&]q=([^&]+).*$'),
		re.compile(r'^http://.*google\..*[\?&]as_q=([^&]+).*$'),
		re.compile(r'^http://.*google\..*[\?&]as_epq=([^&]+).*$'),
		],
	'alltheweb': [
		re.compile(r'^http://.*\.alltheweb\..*[\?&]q=([^&]*).*$'),
		],
	'feedster': [
		re.compile(r'^http://.*\.feedster\..*[\?&]q=([^&]*).*$'),
		re.compile(r'^http://feedster\..*[\?&]q=([^&]*).*$'),
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
		re.compile(r'^http://.*\.yahoo\..*[\?&]va=([^&]*).*$'),
		],
	'altavista': [
		re.compile(r'^http://.*\.altavista\..*[\?&]q=([^&]*).*$'),
		],
	'msn': [
		re.compile(r'^http://search\.msn\..*[\?&]q=([^&]*).*$'),
		re.compile(r'^http://.*\.search\.msn\..*[\?&]q=([^&]*).*$'),
		],
	'blo.gs': [
		re.compile(r'^http://.*blo\.gs\/\?q=([^&]*).*$'),
		],
	'lycos': [
		re.compile(r'^http://.*\.lycos\..*[\?&]query=([^&]*).*$'),
		],
	'aol': [
		re.compile(r'^http://.*\.aol\..*search.jsp.*[\?&]q=([^&]*).*$'),
		re.compile(r'^http://.*\.aol\..*[\?&]query=([^&]*).*$'),
		],
	't-online': [
		re.compile(r'^http://.*\.t-online\..*tsc.*[\?&]q=([^&]*).*$'),
		],
	'Virgilio': [
		re.compile(r'^http://.*\.virgilio\..*search\.cgi\?qs=([^&]*).*$'),
		],
	'mysearch': [
		re.compile(r'^http://.*\.mysearch\..*[\?&]searchfor=([^&]*).*$'),
		re.compile(r'^http://mysearch\..*[\?&]searchfor=([^&]*).*$'),
	],
	'Parnassus': [
		re.compile(r'^http://py.vaults.ca/apyllo.py.*[\?&]find=([^&]*).*$'),
		re.compile(r'^http://www.vex.net/parnassus/apyllo.py.*[\?&]find=([^&]*).*$'),
	],
	'eniro': [
		re.compile(r'^.*\.eniro\.se/query\?.*&q=([^&]*).*$'),
	],
	'netfind': [
		re.compile(r'^.*\.netfind\.de/suche/search.jsp\?q=([^&]*).*$'),
	],
	'naver': [
		re.compile(r'^http://search.naver.com/search.naver.*[\?&]query=([^&]*).*$'),
	],
	'fireball': [
		re.compile(r'^http://suche.fireball.de/suche.csp.*[\?&]q=([^&]*).*$'),
	],
	'blogshares': [
		re.compile(r'^http://blogshares.com/blogs.php\?blog=([^&]*).*$'),
	],
	'technorati': [
		re.compile(r'^http://.*technorati\.com/cosmos/links.html.*[\?&]url=([^&]*).*$'),
	],
	'web.de': [
		re.compile(r'^http://suche.*web.de/search/.*[\?&]su=([^&]*).*$'),
	],
	'rss-search': [
		re.compile(r'^http://.*rss\-search.com/index.cgi/SearchResult\?.*&IR_FreeText=([^&]*).*$'),
	],
	'hotbot': [
		re.compile(r'^http://.*hotbot.com/default.asp.*[\?&]query=([^&]*).*$'),
	],
	'netscape': [
		re.compile(r'^http://.*netscape.*search.jsp.*[\?&]q=([^&]*).*$'),
		re.compile(r'^http://.*netscape.*boomframe.jsp.*[\?&]query=([^&]*).*$'),
	],
	'bbc': [
		re.compile(r'^http://.*bbc.co.uk.*results.pl.*[\?&]q=([^&]*).*$'),
	],
	'blogsuche.de': [
		re.compile(r'http://blogsuche.de/search.php?search=([^&]*).*$'),
	],
	'deutschesuche.de': [
		re.compile(r'http://www.deutschesuche.de/suche.php.*[\?&]?qkw=([^&]*).*$'),
	],
	'tdconline.dk': [
		re.compile(r'http://find.tdconline.dk/google.php?q=([^&]*).*$'),
	],
	'picsearch.de': [
		re.compile(r'http://www.picsearch.de/info.cgi?q=([^&]*).*$'),
	],
	'szukaj.wp.pl': [
		re.compile(r'http://szukaj.wp.pl/szukaj.html?szukaj=([^&]*).*$'),
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


# Python Community Server
#
#     searches.py: Analyse referrers to gather search terms
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


import os
import re
import cgi
import string
import pycs_settings
import time

from urllib import unquote, quote

# format of the entries:
#  first line is a pattern for the search engine to research
#  second to last line are compiled regexps to match for search engines
engines = {
	'google': [ 'http://google.com/search?q=%s',
		re.compile(r'^http://.*\.google\..*[\?&]q=([^&]*).*$'),
		re.compile(r'^http://.*\.google\..*[\?&]as_q=([^&]*).*$'),
		],
	'alltheweb': [ 'http://www.alltheweb.com/search?q=%s',
		re.compile(r'^http://.*\.alltheweb\..*[\?&]q=([^&]*).*$'),
		],
	'feedster': [ 'http://www.feedster.com/search.php?q=%s',
		re.compile(r'^http://.*\.feedster\..*[\?&]q=([^&]*).*$'),
		],
	'freshmeat': [ 'http://freshmeat.net/search/?q=%s',
		re.compile(r'^http://freshmeat\..*[\?&]q=([^&]*).*$'),
		],
	'daypop': [ 'http://www.daypop.com/search?q=%s',
		re.compile(r'^http://.*\.daypop\..*[\?&]q=([^&]*).*$'),
		],
	'geourl': [ 'http://www.geourl.com/near/?p=%s',
		re.compile(r'^http://geourl\..*[\?&]p=([^&]*).*$'),
		],
	'yahoo': [ 'http://search.yahoo.com/search?p=%s',
		re.compile(r'^http://.*\.yahoo\..*[\?&]p=([^&]*).*$'),
		],
	'altavista': [ 'http://www.altavista.com/web/results?q=%s',
		re.compile(r'^http://.*\.altavista\..*[\?&]q=([^&]*).*$'),
		],
	'msn': [ 'http://search.msn.com/results.aspx?q=%s',
		re.compile(r'^http://search\.msn\..*[\?&]q=([^&]*).*$'),
		],
	'blo.gs': [ 'http://blo.gs/?q=%s',
		re.compile(r'^http://blo\.gs\/\?q=([^&]*).*$'),
		],
	'lycos': [ 'http://hotbot.lycos.com/?query=%s',
		re.compile(r'^http://.*\.lycos\..*[\?&]query=([^&]*).*$'),
		],
	'aol': [ 'http://search.aol.com/aolcom/search?query=%s',
		re.compile(r'^http://.*\.aol\..*search.jsp\?q=([^&]*).*$'),
		re.compile(r'^http://.*\.aol\..*[\?&]query=([^&]*).*$'),
		],
	't-online': [ 'http://brisbane.t-online.de/fast-cgi/tsc?q=%s',
		re.compile(r'^http://.*\.t-online\..*tsc\?q=([^&]*).*$'),
		],
	'Virgilio': [ 'http://search.virgilio.it/search/cgi/search.cgi?qs=%s',
		re.compile(r'^http://.*\.virgilio\..*search\.cgi\?qs=([^&]*).*$'),
		],
	'mysearch': [ 'http://www.mysearch.com/jsp/AWmain.jsp?searchfor=%s',
		re.compile(r'^http://.*\.mysearch\..*[\?&]searchfor=([^&]*).*$'),
	],
	}

def sortISOTime(timea,timeb):
	ta = time.strptime(timea.time,'%Y-%m-%d %I:%M:%S %p')
	tb = time.strptime(timeb.time,'%Y-%m-%d %I:%M:%S %p')
	return -1*cmp(ta,tb)
	
request['Content-Type'] = 'text/html'

[path, params, query, fragment] = request.split_uri()
query = util.SplitQuery( query )
form = util.SplitQuery( input_data.read() )

page = {
	'title': _('Zeitgeist overview'),
	'body': """<p>Something went wrong; there should be some text here!</p>
		<p>Mail <a href="http://www.myelin.co.nz/phil/email.php">Phil</a> at 
		<a href="http://www.myelin.co.nz/">Myelin</a> if you
		think something is broken.</p>""",
	}

s = ''

if not query.has_key('usernum'):
	# no usernum specified - dump out a short explanation of why this is bad
	s += """<p>No usernum specified!</p>
	<p>Did you get to this page from a link from your Radio <a href="http://127.0.0.1:5335/">desktop website</a>?
	if so, something is wrong - please mail <a href="http://www.myelin.co.nz/phil/email.php">Phil</a>
	and tell him the software is broken.</p>
	<p>If you got here by editing the URL, try putting something like "?usernum=0000001" at the end;
	that way you can get a summary of hits (by referrer) for a weblog hosted on this server.</p>
	"""
else:

	try:
		usernum = query['usernum']
		try:
			usernum = int(usernum)
		except: pass

		group = query.get('group','default')
		
		user = set.User( usernum )
		url = set.UserFolder( usernum )
		usernum = user.usernum
		
		s += _('<h2>Zeitgeist overview for <strong><a href="%s">%s</a></strong></h2>') % (url, user.name)
		s += _('<p>Here are all search terms which people followed here, sorted by last hit. The larger the font, the more often the term was searched for. The more to the top, the more current was the access.')

		referrerlist = []
		for row in set.referrers.select( { 'usernum': usernum, 'group': group } ):
			referrerlist.append(row)
		referrerlist.sort(sortISOTime)

		searchterms = []
		searchtuples = {}
		for row in referrerlist:
			matched = None
			term = None
			for engine in engines.keys():
				for termre in engines[engine][1:]:
					m = termre.match(row.referrer)
					if m:
						matched = engine
						term = m.group(1)
						while term.find('%') >= 0:
							t = unquote(term)
							if t == term:
								term = t.replace('%', '')
							else:
								term = t
						try:
							term = term.decode('utf-8').encode('iso-8859-1')
						except: pass
			if matched:
				url = row.referrer
				if engines[matched][0]:
					url = engines[matched][0] % quote(term)
				idx = searchtuples.get(url, -1)
				if idx >= 0:
					searchterms[idx][3] += row.count
				else:
					searchtuples[url] = len(searchterms)
					searchterms.append([term, matched, url, row.count])
		counts = {}
		for (term, engine, url, count) in searchterms:
			if counts.has_key(count):
				counts[count] += 1
			else:
				counts[count] = 1
		countcounts = counts.keys()
		countcounts.sort()
		sizes = {}
		i = 10
		for c in countcounts:
			sizes[c] = i
			if i < 16:
				i += 2
			elif i < 24:
				i += 4
			elif i < 36:
				i += 6

		s += '<p>'
		colnr = 0
		color = ('#006666', '#333366', '#669900', '#663399', '#999933', '#009966', '#996699', '#999933', '#669900', '#660033', '#666600', '#336633', '#663333', '#663399', '#990000', '#999966', '#336600', '#660000', '#663333', '#990066', '#339933', '#000033', '#003366', '#666600', '#996633', '#339966', '#990099')
		i = 0
		maxi = len(searchterms) - 1
		for (term, engine, url, count) in searchterms:
			s += '<a style="text-decoration: none; font-size: %dpx; color: %s" href="%s" title="%s">' % ( sizes[count], color[colnr], url, _('accessed %d times') % count )
			s += unquote( term )
			s += '</a>'
			colnr += 1
			if colnr >= len(color):
				colnr = 0
			if i < maxi:
				s += ' &middot; '
				i += 1

	except pycs_settings.NoSuchUser:
		s += _('<p>Sorry, user %s not found!</p>') % (usernum,)
	
# Dump it all out

page['body'] = s
s = set.Render( page, hidden=1 )

request['Content-Length'] = len(s)
request.push( s )
request.done()

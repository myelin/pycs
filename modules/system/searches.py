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

engines = {
	'google': [
		re.compile(r'^http://.*\.google\..*\?q=([^&]*).*$'),
		],
	'yahoo': [
		re.compile(r'^http://.*\.yahoo\..*\?p=([^&]*).*$'),
		],
	}

def orderLink(username,group,order):
	return set.ServerUrl() + '/system/referers.py?usernum=%s&group=%s&order=%s' % (usernum, group, order)

def sortISOTime(timea,timeb):
	ta = time.strptime(timea.time,'%Y-%m-%d %I:%M:%S %p')
	tb = time.strptime(timeb.time,'%Y-%m-%d %I:%M:%S %p')
	return -1*cmp(ta,tb)
	
request['Content-Type'] = 'text/html'

[path, params, query, fragment] = request.split_uri()
query = util.SplitQuery( query )
form = util.SplitQuery( input_data.read() )

page = {
	'title': 'Search term rankings',
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
		order = query.get('order','time')
		
		user = set.User( usernum )
		usernum = user.usernum
		
		s += """
		<h2>Search terms for <strong>%s</strong></h2>
		<table width="80%%" cellspacing="5" cellpadding="2">
		""" % (user.name,)

		if order == 'time':
			s += """
			<tr><th align="left"><a href="%s">Search term</a></th>
				<th align="left">Last hit</th>
				<th align="right"><a href="%s">Count</a></th></tr>
			""" % ( orderLink( usernum, group, 'referrer' ),
				orderLink( usernum, group, 'count' ) )
		elif order == 'count':
			s += """
			<tr><th align="left"><a href="%s">Search term</a></th>
				<th align="left"><a href="%s">Last hit</a></th>
				<th align="right">Count</th></tr>
			""" % (orderLink(usernum, group, 'referrer'),
				orderLink(usernum, group, 'time'))
		else:
			s += """
			<tr><th align="left">Search term</th>
				 <th align="left"><a href="%s">Last hit</a></th>
				<th align="right"><a href="%s">Count</a></th></tr>
			""" % (orderLink(usernum, group, 'time'),
				orderLink(usernum, group, 'count'))

		referrerlist = []
		for row in set.referrers.select( { 'usernum': usernum, 'group': group } ):
			referrerlist.append(row)

		if order == 'time':
			referrerlist.sort(sortISOTime)
		elif order == 'count':
			referrerlist.sort(lambda a,b: -1*cmp(a.count,b.count))
		else:
			referrerlist.sort(lambda a,b: -1*cmp(a.referrer,b.referrer))

		for row in referrerlist:
			matched = None
			term = None
			for engine in engines.keys():
				for termre in engines[engine]:
					m = termre.match(row.referrer)
					if m:
						matched = engine
						term = m.group(1)
			if matched and term:
				s += """
				<tr><td align="left"><a target="_new" href="%s">%s: <b>%s</b></a></td>
				<td align="left"><pre>%s</pre></td><td align="right">%s</td></tr>
				""" % (cgi.escape( row.referrer, 1 ), matched, term, row.time, row.count)

		s += """
		</table>
		<p>See also: <a href="referers.py?usernum=%s&group=%s&order=%s">Referrer rankings for this site</a>.</p>
		""" % (usernum, group, order)

	except pycs_settings.NoSuchUser:
		s += '<p>Sorry, user %s not found!</p>' % (usernum,)
	
# Dump it all out

page['body'] = s
s = set.Render( page )

request['Content-Length'] = len(s)
request.push( s )
request.done()
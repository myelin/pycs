# Python Community Server
#
#     referers.py: Display referrer rankings page for a user
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
import cgi
import string
import pycs_settings
import time
from search_engines import checkUrlForSearchEngine

def orderLink(username,group,order,full):
	if full:
		return set.ServerUrl() + '/system/referers.py?usernum=%s&group=%s&order=%s&full=1' % (usernum, group, order)
	else:
		return set.ServerUrl() + '/system/referers.py?usernum=%s&group=%s&order=%s' % (usernum, group, order)

def sortISOTime(timea,timeb):
	ta = time.strptime(timea.time,'%Y-%m-%d %I:%M:%S %p')
	tb = time.strptime(timeb.time,'%Y-%m-%d %I:%M:%S %p')
	return -1*cmp(ta,tb)
	
request['Content-Type'] = 'text/html; charset=%s' % set.DocumentEncoding()

[path, params, query, fragment] = request.split_uri()
query = util.SplitQuery( query )
form = util.SplitQuery( input_data.read() )

page = {
	'title': _('Referrer rankings'),
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
		full = query.get('full', '')
		if full: full = 1
		else: full = 0
		
		user = set.User( usernum )
		usernum = user.usernum
		
		referrerlist = []
		searchlist = []
		fulllist = []
		data = set.referrers.select( { 'usernum': usernum, 'group': group } )
		for row in data:
			(matched, term) = checkUrlForSearchEngine(row.referrer)
			if not(matched) or not(term):
				referrerlist.append(row)
			else:
				searchlist.append(row)
			fulllist.append(row)

		if len(fulllist) < 100:
			referrerlist = fulllist
			full = 1
		elif len(searchlist) < 30 or len(referrerlist) < 30:
			referrerlist = fulllist
			full = 1

		if order == 'time':
			referrerlist.sort(sortISOTime)
		elif order == 'count':
			referrerlist.sort(lambda a,b: -1*cmp(a.count,b.count))
		else:
			referrerlist.sort(lambda a,b: -1*cmp(a.referrer,b.referrer))

		s += "<h2>%s <strong>%s</strong></h2>" % (
			_('Referrers for'),
			user.name,
		)
		s += _("<p>This page shows you where the hits on your weblog came from.")
		if not full:
			s += _(' Search engine hits are excluded: to see all referrers, <a href="referers.py?usernum=%s&group=%s&order=%s&full=1">click here</a>.') % (usernum, group, order)
		s += '<p><table width="80%%" cellspacing="5" cellpadding="2">'

		if order == 'time':
			s += """
			<tr><th align="left"><a href="%s">%s</a></th>
				<th align="left">%s</th>
				<th align="right"><a href="%s">%s</a></th></tr>
			""" % ( orderLink( usernum, group, 'referrer', full ),
			        _('Referrer'),
				_('Last hit'),
				orderLink( usernum, group, 'count', full ),
				_('Count') )
		elif order == 'count':
			s += """
			<tr><th align="left"><a href="%s">%s</a></th>
				<th align="left"><a href="%s">%s</a></th>
				<th align="right">%s</th></tr>
			""" % ( orderLink(usernum, group, 'referrer', full),
			        _('Referrer'),
				orderLink(usernum, group, 'time', full),
				_('Last hit'),
				_('Count') )
		else:
			s += """
			<tr><th align="left">%s</th>
				 <th align="left"><a href="%s">%s</a></th>
				<th align="right"><a href="%s">%s</a></th></tr>
			""" % ( _('Referrer'),
			        orderLink(usernum, group, 'time', full),
				_('Last hit'),
				orderLink(usernum, group, 'count', full),
				_('Count') )

		for row in referrerlist:
			referrer = cgi.escape( row.referrer, 1 )
			if len(referrer) > 44:
				referrer = referrer[:40] + ' [...]'
			referrer = referrer.replace(' ','&nbsp;')

			s += """
			<tr><td align="left"><a target="_new" href="%s">%s</a></td>
			<td align="left"><pre>%s</pre></td><td align="right">%s</td></tr>
			""" % ( row.referrer, referrer, row.time, row.count)

		s += "</table>\n"
		s += _('<p>See also: <a href="searches.py?usernum=%s&group=%s&order=%s">Search term rankings for this site</a>.</p>') % (usernum, group, order)

	except pycs_settings.NoSuchUser:
		s += _('<p>Sorry, user %s not found!</p>') % (usernum,)
	
# Dump it all out

page['body'] = s
s = set.Render( page, hidden=1 )

request['Content-Length'] = len(s)
request.push( s )
request.done()

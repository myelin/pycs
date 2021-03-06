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
from urllib import unquote
from search_engines import checkUrlForSearchEngine
from string_collector import StringCollector

def orderLink(username,group,order):
	return set.ServerUrl() + '/system/searches.py?usernum=%s&group=%s&order=%s' % (usernum, group, order)

def sortISOTime(timea,timeb):
	ta = time.strptime(timea.time,'%Y-%m-%d %I:%M:%S %p')
	tb = time.strptime(timeb.time,'%Y-%m-%d %I:%M:%S %p')
	return -1*cmp(ta,tb)
	
request['Content-Type'] = 'text/html; charset=%s' % set.DocumentEncoding()

[path, params, query, fragment] = request.split_uri()
query = util.SplitQuery( query )
form = util.SplitQuery( input_data.read() )

page = {
	'title': _('Search term rankings'),
	'body': """<p>Something went wrong; there should be some text here!</p>
		<p>Mail <a href="http://www.myelin.co.nz/phil/email.php">Phil</a> at 
		<a href="http://www.myelin.co.nz/">Myelin</a> if you
		think something is broken.</p>""",
	}

s = StringCollector(set.DocumentEncoding())

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
		usernum = int(user.usernum)
		
		s += _("<h2>Search terms for <strong>%s</strong></h2>") % (user.name,)
		s += '<table width="80%%" cellspacing="5" cellpadding="2">'

		if order == 'time':
			s += """
			<tr><th align="left"><a href="%s">%s</a></th>
				<th align="left">%s</th>
				<th align="right"><a href="%s">%s</a></th></tr>
			""" % ( orderLink( usernum, group, 'word' ),
			        _("Search term"),
				_("Last hit"),
				orderLink( usernum, group, 'count' ),
				_("Count") )
		elif order == 'count':
			s += """
			<tr><th align="left"><a href="%s">%s</a></th>
				<th align="left"><a href="%s">%s</a></th>
				<th align="right">%s</th></tr>
			""" % ( orderLink(usernum, group, 'word'),
			        _("Search term"),
				orderLink(usernum, group, 'time'),
				_("Last hit"),
				_("Count") )
		else:
			s += """
			<tr><th align="left">%s</th>
				 <th align="left"><a href="%s">%s</a></th>
				<th align="right"><a href="%s">%s</a></th></tr>
			""" % ( _("Search term"),
			        orderLink(usernum, group, 'time'),
				_("Last hit"),
				orderLink(usernum, group, 'count'),
				_("Count") )

		if order == 'time':
			order_criteria = 'hit_time'
		elif order == 'count':
			order_criteria = 'hit_count'
		else:
			order_criteria = 'referrer'

		for hit_time, full_referrer, hit_count, engine, term in set.pdb.execute("SELECT hit_time, referrer, hit_count, search_engine, search_term FROM pycs_referrers WHERE usernum=%d AND usergroup=%s AND is_search_engine='t' ORDER BY "+order_criteria+" DESC LIMIT 100", (usernum, group)):
			try:
				term = term.decode('utf-8').encode('iso-8859-1')
			except: pass
			s += """
			<tr><td align="left"><a target="_new" href="%s">%s: <b>%s</b></a></td>
			<td align="left"><pre>%s</pre></td><td align="right">%s</td></tr>
			""" % ( full_referrer.replace('"','%22'), engine, unquote( term ), hit_time, hit_count)

		s += "</table>\n"
		s += _('<p>See also: <a href="referers.py?usernum=%s&group=%s&order=%s">Referrer rankings for this site</a>.</p>') % (usernum, group, order)

	except pycs_settings.NoSuchUser:
		s += _('<p>Sorry, user %s not found!</p>') % (usernum,)
	
# Dump it all out

page['body'] = str(s)
s = set.Render( page, hidden=1 )

request['Content-Length'] = len(s)
request.push( s )
request.done()

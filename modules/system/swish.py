# Python Community Server
#
#     swish.py: do a search on your pages using swish
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
import time
import pycs_settings
import pycs_paths

request['Content-Type'] = 'text/html'

[path, params, query, fragment] = request.split_uri()
query = util.SplitQuery( query )
form = util.SplitQuery( input_data.read() )

page = {
	'title': _('Search your Weblog'),
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
elif not query.has_key('q'):
	s += """<p>%s</p>

	<p>
	<form method="get" action="%s">
		<input type="hidden" name="usernum" value="%s">
		<input type="text" name="q" size="40">
		<input type="submit" value="%s">
	</form>
	</p>
	""" % (
		_('Enter the words to search for:'),
		cgi.escape(path, 1),
		cgi.escape(query['usernum'], 1),
		_('Search')
	)
else:

	try:
		usernum = query['usernum']
		try:
			usernum = int(usernum)
		except: pass

		group = query.get('group','default')

		term = query['q']
		term = re.sub( '[^a-zA-Z0-9_\-\ ]', '', term )
		
		user = set.User( usernum )
		url = set.UserFolder( usernum )
		usernum = user.usernum
		
		s += _('<h2>Search results for <strong>%s</strong></h2>') % term
		s += _('<p>Here are all search results while searching for <strong>%s</strong> on the weblog of <a href="%s">%s</a>.') % (
			term,
			url,
			user.name
		)

		cmd = "search++ -i %s '%s'" % (
			os.path.join(pycs_paths.VARDIR, 'swish++', usernum, 'swish++.index'),
			term
		)
		
		print cmd

		s += '<table border=0 cellspacing=5 cellpadding=5>'
		s += '<tr><th>%s</th><th>%s</th><th>%s</th></tr>' % (
			_('Rank'),
			_('Page'),
			_('Size')
		)
		for line in os.popen(cmd).readlines():
			if line[-1] == '\n': line = line[:-1]

			if line and line[0] != '#':
				s += '<tr>'
				(rank, path, psize, title) = line.split(' ', 3)

				lpath = os.path.join(pycs_paths.WEBDIR, 'users', usernum)
				if len(path) > len(lpath):
					if path[:len(lpath)] == lpath:
						path = path[len(lpath):]
	
				resurl = url + path[1:]
				
				s += '<td>%s</td>' % rank
				s += '<td>'
				s += '<a href="%s" title="%s">' % ( resurl, title )
				s += title
				s += '</a>'
				s += '</td>'
				s += '<td>%s %s</td>' % ( psize, _('Bytes') )
				s += '</tr>'
		s += '</table>'

	except pycs_settings.NoSuchUser:
		s += _('<p>Sorry, user %s not found!</p>') % (usernum,)
	
# Dump it all out

page['body'] = s
s = set.Render( page, hidden=1 )

request['Content-Length'] = len(s)
request.push( s )
request.done()

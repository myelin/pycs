# Python Community Server
#
#     users.py: User info view page
#
# Copyright (c) 2002, Phillip Pearson <pp@myelin.co.nz>
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


import string
import md5
import pycs_settings
import cgi

def esc(s):
	return cgi.escape(s, 1)

request['Content-Type'] = 'text/html; charset=%s' % set.DocumentEncoding()

[path, params, query, fragment] = request.split_uri()
query = util.SplitQuery( query )
form = util.SplitQuery( input_data.read() )

page = {
	'title': _('User info'),
	'body': """<p>Something went wrong; there should be some text here!</p>
		<p>Mail <a href="mailto:pp@myelin.co.nz">Phil</a> at 
		<a href="http://www.myelin.co.nz/">Myelin</a> if you
		think something is broken.</p>""",
	}

s = ''

# Are we viewing/editing someone?
if query.has_key('usernum'):

	try:
		usernum = query['usernum']
		
		user = set.User( usernum )
		
		s += """
		<h2>%s #<strong>%s</strong></h2>
		<table width="80%%" cellspacing="0" cellpadding="2">
		""" % ( _("Information for user"), usernum,)
		
		cols = {}
		
		for col in set.users.structure():
			cols[col.name] = getattr( user, col.name )
		
		# Get rid of ones we don't want people to see
		del cols['password']
		del cols['serialNumber']
		
		url = set.UserFolder( usernum )
		cols['url'] = '<a href="%s">%s</a>' % ( url, url )
		
		localpart, domain = string.split( cols['email'], '@' )
		nospamemail = '%s at %s' % ( localpart, domain )
		cols['email'] = '<a href="mailto.py?usernum=%s">%s</a>' % ( cols['usernum'], nospamemail )
	
		clist = cols.keys()
		clist.sort()
		for col in clist:
			
			s += '<tr><td>%s</td><td><strong>%s<strong></td></tr>' % ( col, cols[col] )
		
		s += """
		</table>
		"""
	
	except pycs_settings.NoSuchUser:
		s += _('<p>Sorry, user %s not found!</p>') % (usernum,)

else:

	if query.get('format', '') == 'rss':
		s += '<?xml version="1.0" encoding="%s"?>' % set.DocumentEncoding()
		s += '<rss version="2.0">'
		s += '<channel>'
		s += '<title>%s</title>' % _('RSS feed of users')
		s += '</channel>'
		for user in set.users:
			url = set.UserFolder( user.usernum )
			s += '<item>'
			s += '<title>%s (%d)</title>' % (
				esc(user.name),
				int(user.usernum)
			)
			s += '<link>%s</link>' % url
			s += '<description>%s</description>' % esc(user.weblogTitle)
			s += '</item>'
		s += '</rss>'
	else:
		s += _('<p>This is a list of all users registered on this server:')
		s += '<ul>'
		for user in set.users:
			url = set.UserFolder( user.usernum )
			s += '<li><strong>%d</strong> <a href="%s">%s</a> - %s</li>' % (
				int(user.usernum),
				url,
				user.name,
				user.weblogTitle
			)
		s += '</ul>'

# Dump it all out

if query.get('format', '') == 'rss':
	request['Content-Type'] = 'text/xml'
else:
	page['body'] = s
	s = set.Render( page )

request['Content-Length'] = len(s)
request.push( s )
request.done()

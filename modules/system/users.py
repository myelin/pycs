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
		mirror = set.mirrored_posts.find(usernum=user.usernum)
		if mirror == -1:
			cols['search_index_active'] = 0
		else:
			cols['search_index_active'] = 1
			cols['search_index_posts'] = len(set.mirrored_posts[mirror].posts)
		
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

	sort_spec = query.get('sort', 'usernum')
	if sort_spec not in ('usernum', 'space'):
		s += "<p>Invalid sort specifier!</p>"

	elif query.get('format', '') == 'rss':
		s += '<?xml version="1.0" encoding="%s"?>\n' % set.DocumentEncoding()
		s += '<rss version="2.0">\n'
		s += '<channel>\n'
		s += '<title>%s</title>\n' % _('RSS feed of users')
		s += '<link>%s</link>\n' % set.ServerUrl()
		s += '<description>%s</description>\n' % _('RSS feed of all blogs and users registered on this community server')
		liste = []
		for user in set.users:
			url = set.UserFolder( user.usernum )
			liste.append((user.name, user.usernum, user.weblogTitle, url))
		liste.reverse()
		if len(liste) > 30:
			liste = liste[:30]
		for (name, usernum, weblogTitle, url) in liste:
			s += '<item>\n'
			s += '<title>%s (%d)</title>\n' % (
				esc(name),
				int(usernum)
			)
			s += '<link>%s</link>\n' % url
			s += '<description>%s</description>\n' % esc(weblogTitle)
			s += '</item>\n'
		s += '</channel>\n'
		s += '</rss>\n'
	else:
		s += _('<p>This is a list of all users registered on this server:</p>')
		s += '<p><a href="users.py?format=rss">RSS</a> | <a href="users.py?sort=usernum">%s</a> | <a href="users.py?sort=space">%s</a></p>' % (_('sort by usernum'), _('sort by space used'))
		s += '<ul>'
		users = []
		for user in set.users:
			url = set.UserFolder( user.usernum )
			if sort_spec == 'usernum':
				sort_key = int(user.usernum)
			elif sort_spec == 'space':
				sort_key = user.bytesused
			user_info = (
				int(user.usernum),
				url,
				user.name,
				user.weblogTitle,
				set.SpaceString(user.bytesused),
			)
			users.append((sort_key, user_info))
		users.sort()
		for user in users:
			s += '<li><strong>%d</strong> <a href="%s">%s</a> - %s (%s)</li>' % user[1]
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

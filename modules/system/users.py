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


import md5
import pycs_settings

request['Content-Type'] = 'text/html'

[path, params, query, fragment] = request.split_uri()
query = util.SplitQuery( query )
form = util.SplitQuery( input_data.read() )

page = {
	'title': 'User info',
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
		<h2>Information for user #<strong>%s</strong></h2>
		<table width="80%%" cellspacing="0" cellpadding="2">
		""" % (usernum,)
		
		cols = {}
		
		for col in set.users.structure():
			cols[col.name] = getattr( user, col.name )
		
		# Get rid of ones we don't want people to see
		del cols['password']
		del cols['serialNumber']
		
		url = set.UserFolder( usernum )
		cols['url'] = '<a href="%s">%s</a>' % (url, url)
		
		cols['email'] = '<a href="mailto.py?usernum=%s">%s</a>' % (cols['usernum'], cols['email'])
		
		for col in cols.keys():
			
			s += '<tr><td>%s</td><td><strong>%s<strong></td></tr>' % ( col, cols[col] )
		
		s += """
		</table>
		"""
	
	except pycs_settings.NoSuchUser:
		s += '<p>Sorry, user %s not found!</p>' % (usernum,)
	
# Dump it all out

page['body'] = s
s = set.Render( page )

request['Content-Length'] = len(s)
request.push( s )
request.done()

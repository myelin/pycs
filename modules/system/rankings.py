# Python Community Server
#
#     rankings.py: Display hit counts and rankings for all users
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


import os
import string
import pycs_settings
import pycs_paths

request['Content-Type'] = 'text/html'

[path, params, query, fragment] = request.split_uri()
query = util.SplitQuery( query )
form = util.SplitQuery( input_data.read() )

page = {
	'title': _('Rankings'),
	'body': """<p>Something went wrong; there should be some text here!</p>
		<p>Mail <a href="http://www.myelin.co.nz/phil/email.php">Phil</a> at 
		<a href="http://www.myelin.co.nz/">Myelin</a> if you
		think something is broken.</p>""",
	}

s = ''


todayRanks = []
alltimeRanks = []

for user in set.users:
	todayRanks.append( ( user.hitstoday, user ) )
	alltimeRanks.append( ( user.hitsalltime, user ) )

for section in ( todayRanks, alltimeRanks ):
	section.sort()
	section.reverse()

s += """
<table width="80%">
<tr>
"""

for title,section in ( (_("hits today"),todayRanks), (_("all-time hits"),alltimeRanks) ):
	s += """
	<td>
	<table width="100%%" cellspacing="0" cellpadding="2">
	<thead>
		<tr><td>""" + _("blog name") + """</td><td>%s</td></tr>
	</thead>
	<tbody>
	""" % ( title, )

	for hits,user in section:
		if not hits: break
		s += """
		<tr><td><a href="%s">%s</a> (<a href="%s">%s</a>)</td><td>%d</td></tr>
		""" % ( "referers.py?usernum=%s&order=count" % ( user.usernum, ),
			user.weblogTitle, set.UserFolder( user.usernum ),
			_("link"), hits
		)

	s += """
	</tbody>
	</table>
	</td>
	"""

s += """
</tr>
</table>
""" + _('<p>See also: <a href="weblogUpdates.py">weblogs updated today</a>.</p>\n')

# Dump it all out

page['body'] = s
s = set.Render( page )

request['Content-Length'] = len(s)
request.push( s )
request.done()

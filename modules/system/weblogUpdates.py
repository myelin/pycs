# Python Community Server
#
#     weblogUpdates.py: Recently updated pages list (from XML-RPC calls to weblogUpdates.ping())
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


import md5, time
import cgi
import re

request['Content-Type'] = 'text/html; charset=%s' % set.DocumentEncoding()

page = {
	'title': _('Recently updated weblogs'),
	'body': """<p>Something went wrong; there should be some text here!</p>
		<p><a href="mailto:pp@myelin.co.nz">Mail Phil</a> at 
		<a href="http://www.myelin.co.nz/">Myelin</a> if you
		think something is broken.</p>""",
	}

s = _("<p>Here are the weblogs that have updated in the last 24 hours.  Is yours in there?  ;-)</p>")
s += '\n<table width="80%" cellspacing="0" cellpadding="2">'

# get rid of old updates
set.pdb.execute("DELETE FROM pycs_updates WHERE update_time < CURRENT_TIMESTAMP - INTERVAL '24 HOURS'")

# now run through all updates and make a row for each ('1. | My blog | 2002-03-22 03:30 AM')
nDispIndex = 1
for update_time, how_long_ago, blog_url, blog_title in set.pdb.execute("SELECT DATE_TRUNC('minute', update_time), DATE_TRUNC('second', CURRENT_TIMESTAMP - update_time), url, title FROM pycs_updates ORDER BY update_time DESC"):
	# work out how long ago
	# munge blog name to display properly in HTML
	blog_title = blog_title.replace('&apos;', "'")
	blog_title = re.sub(r'\<.*?\>', '', blog_title)
	# display line
	s += """
	<tr>
	<td>%d.</td>
	<td><strong><a href="%s">%s</a></strong></td>
	<td><strong>%s (%s ago)</strong></td>
	</tr>
	""" % ( nDispIndex, blog_url, blog_title,
		update_time.strftime("%I:%m %p"),
		int(how_long_ago.hours) and ("%d h" % how_long_ago.hours) or int(how_long_ago.minutes) and ("%d m" % how_long_ago.minutes) or ("%d s" % how_long_ago.seconds),
#		time.strftime( '%Y-%m-%d %I:%M %p', time.localtime( u.updateTime ) )
		)
	nDispIndex += 1
if nDispIndex == 1:
	s += '<tr><td>(none)</td></tr>'
		
s += "</table>\n"
s += _('<p>See also: <a href="rankings.py">most popular weblogs, ranked by page views</a>.</p>')

# Dump it all out

page['body'] = s
s = set.Render( page )

request['Content-Length'] = len(s)
request.push( s )
request.done()

# Python Community Server
#
#     updates.py: Recently updated pages list
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

page = {
	'title': 'Recently updated weblogs',
	'body': """<p>Something went wrong; there should be some text here!</p>
		<p>Mail <a href="mailto:pp@myelin.co.nz">Phil</a> at 
		<a href="http://www.myelin.co.nz/">Myelin</a> if you
		think something is broken.</p>""",
	}

s = """

<p>(This isn't a very reliable updates page; you probably want the <a 
href="weblogUpdates.py">weblogUpdates page</a> - it's much better!)</p>

<table width="80%%" cellspacing="0" cellpadding="2">
"""

if len(set.updates) == 0:
	s += '<tr><td>(none)</td></tr>'
else:
	# Run through all updates and make a row for each ('1. | My blog | 2002-03-22 03:30 AM')
	nDispIndex = 1
	for nIndex in range( len( set.updates ), 0, -1 ):
		u = set.updates[nIndex - 1]
		s += """
		<tr>
		<td>%d.</td>
		<td><strong><a href="%s">%s</a></strong></td>
		<td><strong>%s</strong></td>
		</tr>
		""" % ( nDispIndex, set.UserFolder( u.usernum ), set.User( u.usernum ).weblogTitle, u.time )
		nDispIndex += 1
		
s += """
</table>
"""
	
# Dump it all out

page['body'] = s
s = set.Render( page )

request['Content-Length'] = len(s)
request.push( s )
request.done()

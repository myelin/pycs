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
import string
import pycs_settings
import pycs_paths

request['Content-Type'] = 'text/html'

[path, params, query, fragment] = request.split_uri()
query = util.SplitQuery( query )
form = util.SplitQuery( input_data.read() )

page = {
	'title': 'Referrer rankings',
	'body': """<p>Something went wrong; there should be some text here!</p>
		<p>Mail <a href="http://www.myelin.co.nz/phil/email.php">Phil</a> at 
		<a href="http://www.myelin.co.nz/">Myelin</a> if you
		think something is broken.</p>""",
	}

s = ''

if not query.has_key('usernum'):
	# no usernum specified - dump out a short explanation of why this is bad
	page['body'] = """<p>No usernum specified!</p>
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
		
		user = set.User( usernum )
		usernum = getattr(user,'usernum')
	
		s += """
		<h2>Referrers for <strong>%s</strong></h2>
		<table width="80%%" cellspacing="0" cellpadding="2">
		""" % (user.name,)

		referers = {}
		for log in ('referer.log', 'referer.log.1'):
			basename = '%s-%s' % (usernum, log)
			lfname = os.path.join(pycs_paths.LOGDIR, basename)
			if os.path.exists(lfname):
				LOG = open(lfname)
				line = LOG.readline()
				while line:
					felder = string.split(line)
					time = felder[0]
					referer = '(no referer given)'
					if len(felder) == 5:
						referer = felder[4]
					if referers.has_key(referer):
						referers[referer] = referers[referer] + 1
					else:
						referers[referer] = 1
					line = LOG.readline()
				LOG.close()

		refererlist = referers.items()
		refererlist.sort(lambda a,b: -1*cmp(a[1],b[1]))

		s += """
		<tr><th align="left">Referrer</th><th align="right">Count</th></tr>
		"""

		for (referer, count) in refererlist:
			s += """
			<tr><td align="left">%s</td><td align="right">%s</td></tr>
			""" % (referer, count)

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

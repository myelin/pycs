# Python Community Server
#
#     count.py: Simple counter CGI for referrer tracking behind Apache
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
import time
import pycs_paths
import pycs_settings

request['Content-Type'] = 'image/gif'

[path, params, query, fragment] = request.split_uri()
query = util.SplitQuery( query )
form = util.SplitQuery( input_data.read() )

# Are we called by a page via the standard javascript code?
if query.has_key('usernum'):
	try:
		usernum = query['usernum']
		user = set.User(usernum)
		group = query['group']
		referer = query['referer']
		time = time.strftime('%d/%b/%Y:%H:%M:%S %Z',time.localtime(time.time()))
		usernum = getattr(user,'usernum')
		log = open(os.path.join(pycs_paths.LOGDIR, '%s-referer.log' % usernum), 'a')
		log.write('%s\t%s\t%s\t%s\n' % (time, usernum, group, referer))
		log.close()
	except pycs_settings.NoSuchUser:
		pass
	
# Dump a blank gif
gifstr = """47 49 46 38 39 61 01 00 01 00 B3 00 00 00 00 00
            00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
            00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
            00 00 00 00 00 00 00 00 00 00 00 00 00 21 F9 04
            01 00 00 00 00 2C 00 00 00 00 01 00 01 00 00 04
            02 10 44 00 3B"""

gif = ''
for byte in string.split(gifstr):
	if (byte):
		gif = gif + chr(string.atoi(byte,16))

request['Content-Length'] = len(gif)
request.push( gif )
request.done()


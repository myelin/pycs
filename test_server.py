#!/usr/bin/python

# Python Community Server
#
#     test_server.py: Quick xmlStorageSystem API test
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


import xmlrpclib
import md5

def test_server( s ):
	print
	print "Testing server",s
	radio = xmlrpclib.Server( s )
	xss = radio.xmlStorageSystem
	rcs = radio.radioCommunityServer

	print "radioCommunityServer.getInitialResources"
	print rcs.getInitialResources()
	
	email = 'pycs_test@myelin.co.nz'
	name = 'Test user'
	usernum = '0000001'
	plainPassword = ''
	password = md5.md5( plainPassword ).hexdigest()
	clientPort = 80
	userAgent = 'Python Community Server Test (test_server.py) - http://rcs.myelin.cjb.net/users/0105256/'

	#print "registerUser"
	#print xss.registerUser( email, name, password, clientPort, userAgent )
	
	print "getServerCapabilities"
	caps = xss.getServerCapabilities( usernum, password )
	for k in caps.keys():
		print "key",k,"=",caps[k]

	print "ping"
	print xss.ping( usernum, password, 0, clientPort,
		{
			'email': email,
			'weblogTitle': 'random bloggings',
			'serialNumber': '',
			'organization': 'poor',
			'flBehindFirewall': xmlrpclib.True,
			'name': 'me!'
		} )
		
	
	print "saveMultipleFiles"
	print xss.saveMultipleFiles(
		usernum, password,
		[
			'test.html', 'blah/this_is_ok.html'
		],
		[
			xmlrpclib.Binary('<html><head><title>Foo!</title></head><body><h1>Foo!</h1></body></html>'),
			'<html><head><title>Foo!</title></head><body><h1>Foo!</h1><p>(text)</p></body></html>'
		],
		)

if __name__ == '__main__':
	test_server( 'http://localhost:5445/RPC2' )
	#test_server( 'http://rcs.userland.com:80/RPC2' )
	#test_server( 'http://euro.weblogs.com:80/RPC2' )
	#test_server( 'http://www.blognewsnetwork.com:5335/RPC2' )
	#test_server( 'http://radio.aiesec.ws/RPC2' )
	#test_server( 'http://radio.xmlstoragesystem.com:80/RPC2' )

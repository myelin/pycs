#!/usr/bin/python

# Python Community Server
#
#     changepasswd.py: Set user's passwords from the command line
#
#	WARNING: server must be halted for this to not frag the database!
#
# Copyright (c) 2002, Scott Lewis <scott@bandwidthcoop.org>
#                 and Phillip Pearson <pp@myelin.co.nz>
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

import pycs_settings
import md5, getopt, sys

def usage():
	return """
usage:
  python """ + sys.argv[0] + """ [-h|-?] [-v] -u usernum -p password

    -h, -?        help; print this message
    -l            list users; prints a list of users
    -u usernum	
    -p password   the new password; the hash is stored in the user database
"""

class Fail:
	def __init__( self, msg=None ):
		self.msg = msg
	def show( self ):
		print usage()
		if self.msg:
			print self.msg

class FailQuietly( Fail ):
	def show( self ):
		pass

def main():
	usernum = 0
	password = ''
	
	strShort = 'vh?p:u:l'
	try:
		opts, pargs = getopt.getopt( sys.argv[1:], strShort )
	except getopt.GetoptError:
		raise Fail()
	
	set = pycs_settings.Settings( quiet=True )
	
	for t in opts:
		if t[0] == '-v' or t[0] == '-?':
			verbose = 1
		elif t[0] == '-p':
			password = t[1]
		elif t[0] == '-u':
			usernum = t[1]
		elif t[0] == '-l':
			set.DumpData()
			raise FailQuietly()
		elif t[0] == '-h':
			raise Fail()
	
	if not (usernum and password):
		raise Fail()
	
	try: u = set.User( usernum )
	except pycs_settings.NoSuchUser:
		raise FailQuietly()
	
	s = md5.md5( password ).hexdigest()
	u.password = s
	u.save()
	print 'Password changed for user %s (%s)' % ( usernum, u.email )

if __name__ == '__main__':
	try:
		main()
	except Fail, e:
		e.show()

#!/usr/bin/python

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
	set.Commit()
	print 'Password changed for user %s (%s)' % ( usernum, u.email )

if __name__ == '__main__':
	try:
		main()
	except Fail, e:
		e.show()

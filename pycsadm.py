#!/usr/bin/python

import os
import sys
import sha
import string
import getopt
import xmlrpclib
import pycs_tokens

def usage():
	print "pycsadm [-h]"
	print "   Shows this page of help."
	print ""
	print "pycsadm [-v] [-u <xmlrpc-url>] <cmd> <args>..."
	print "   Executes the command <cmd> on server <xmlrpc-url> with parameters <args>"
	print "   and in the context of user <user>. Use the <cmd> help to get a list of"
	print "   defined commands in your context."
	print ""
	sys.exit(0)

verbose = 0
url = 'http://localhost:5445/RPC2'

(o,args) = getopt.getopt( sys.argv[1:],'hvu:' )
for opt in o:
	if opt[0] == '-h':
		usage()
	elif opt[0] == '-v':
		verbose = 1
	elif opt[0] == '-u':
		url = opt[1]

if not( args ):
	usage()

passwords = {}
cfgfn = os.path.join( os.environ['HOME'], '.pycsadmrc' )
if os.path.exists( cfgfn ):
	pwfile = open(cfgfn)
	line = pwfile.readline()
	while line:
		line = string.strip(line)
		parts = string.split(line, ' = ')
		passwords[parts[0]] = parts[1]
		line = pwfile.readline()

if not( passwords.has_key( url ) ):
	print "Password for server at %s:" % url
	password = sys.stdin.readline()
	password = string.strip( password )
	passwords[url] = password
	pwfile = open( cfgfn, 'w' )
	os.chmod( cfgfn, 0700 )
	for u in passwords.keys():
		pwfile.write( '%s = %s\n' % ( u, passwords[u] ) )
	pwfile.close()

server = xmlrpclib.Server(url)

if verbose:
	print "== get challenge"

challenge = server.pycsAdmin.challenge()
token = pycs_tokens.createToken( passwords[url], challenge )

if verbose:
	print "== execute %s(%s)" % ( args[0], string.join( args[1:],',' ) )

res = server.pycsAdmin.execute( token, args[0], args[1:] )
if res['flError']:
	print "Error: %s" % ( res['message'] )
	sys.exit(8)
else:
	if res.has_key( 'columns' ) and res.has_key( 'table' ):
		print string.join( res['columns'], '\t' )
		lines = []
		for c in res['columns']:
			lines.append( '-' * len( c ) )
		print string.join( lines, '\t' )
		for row in res['table']:
			s = string.join( row, '\t' )
			if type(s) == type(u''):
				s = s.encode('ISO-8859-1')
			print s
	print res['message']


#!/usr/bin/python

import os
import sys
import sha
import string
import getopt
import xmlrpclib
import pycs_tokens
import pycs_settings

set = pycs_settings.Settings( quiet=True, nomk=True )

def usage():
	print """pycsadm [-h]
   Shows this page of help.

pycsadm [-v] [-u <xmlrpc-url>] <cmd> <args>...
   Executes the command <cmd> on server <xmlrpc-url> with parameters <args>
   and in the context of user <user>. Use the <cmd> help to get a list of
   defined commands in your context.

pycsadm add_comments usernum commentfilename
   Imports saved comments from a file 'commentfilename' (in Python script format;
   ask on the pycs-devel mailing list if you want to generate one) to a usernum
   'usernum'.  e.g. pycsadm add_comments 0000999 mycomments.py

   Sometimes you need to run this one twice to import all the comments.  It won't
   add duplicate comments, so you can run it as many times as you like.
"""
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

server = xmlrpclib.Server(url, verbose=verbose)

if verbose:
	print "== get challenge"

def get_token():
	challenge = server.pycsAdmin.challenge()
	token = pycs_tokens.createToken( passwords[url], challenge )
	return token
token = get_token()

cmd = args[0]
params = args[1:]

if verbose:
	print "== execute %s(%s)" % ( cmd, string.join( params,',' ) )

if cmd == 'add_comments':
	usernum, fn, = params
	ns = {}
	execfile(fn, ns, ns)
	# prepare to call
	cmts = ns['comments']
	for k,v in cmts.items():
		print "add comment %s" % k
		for c in v:
			for a,b in c.items():
				if type(b) == type(''):
					c[a] = b.decode('iso-8859-1')
		xrp = [usernum, {k:v}]
		open('xml.xml', 'wt').write(xmlrpclib.dumps((xrp,)))
		res = server.pycsAdmin.execute(token, cmd, xrp)
		print res['message']
		token = get_token()
else:
	res = server.pycsAdmin.execute( token, cmd, params )

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
				s = s.encode(set.DocumentEncoding())
			print s
	print res['message']


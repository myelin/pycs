#!/usr/bin/env python

"""MyMetakit: Metakit-like interface for MySQL

A wrapper to aid in porting applications designed for Metakit to MySQL.

Part of the Python Community Server - http://www.pycs.net/
"""

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

__author__ = 'Phillip Pearson; http://www.myelin.co.nz/'
__license__ = 'MIT; http://www.opensource.org/licenses/mit-license.php'

from __future__ import generators
from pprint import pprint
import MySQLdb
import os.path
import types

class tablecol:
	pass

def tokenize( txt ):
	"Split a line of text into alphanumeric chunks and non-alphanumeric characters"
	s = ''
	for c in txt:
		if c.isalnum() or c == '_':
			s += c
		else:
			if s:
				#print "[string " + s + "]"
				yield s
				s = ''
			yield c

PRIMARY=1
FOREIGN=2
_keynames = {
	None: 'None',
	1: 'Primary',
	2: 'Foreign',
}

class tablecol:
	def __init__( self, name, datatype, keytype=None ):
		self.name = name
		self.datatype = datatype
		self.keytype = keytype
	def __repr__( self ):
		return "<tablecol: name=%s, type=%s, keytype=%s>" % (
			self.name,
			self.datatype,
			_keynames[ self.keytype ],
		)

class tabledef:
	def __init__( self, desc ):
		tokens = tokenize( desc )
		try:
			self.cols = self.parseOne( tokens, 1 )
		except StopIteration:
			raise "Table definition incomplete: %s" % ( desc, )
	def parse( self, tokens, isRoot=0 ):
		"Parse a string into a table definition.  Add an ID column.  If isRoot=0, add a parent ID column so we can connect this back to the parent."
		cols = [ tablecol( 'id', 'integer', PRIMARY ) ]
		if not isRoot:
			cols.append( tablecol( 'parentId', 'integer', FOREIGN ) )
		while 1:
			cols.append( self.parseOne( tokens ) )
			try:
				nextTok = tokens.next()
				if nextTok == ']':
					return ( cols, nextTok )
				elif nextTok == ',':
					pass
				else:
					raise "Syntax error: '%s' found where ']' or ',' expected" % ( nextTok, )
			except StopIteration:
				# done!
				return ( cols, None )
		raise "Internal error: shouldn't get here ;)"
	def parseOne( self, tokens, isRoot=0 ):
		name = tokens.next()
		sep = tokens.next()
		if sep == '[':
			defs, nextTok = self.parse( tokens, isRoot )
			assert( nextTok == ']' )
			return ( name, defs )
		elif sep == ':':
			vartype = tokens.next()
			mkTypes = {
				'I': 'int',
				'S': 'mediumtext',
			}
			if mkTypes.has_key( vartype ):
				return tablecol( name, mkTypes[ vartype ] )
			else:
				raise "Unknown type: '%s'" % ( vartype, )
		raise "Internal error: shouldn't get here!"
	def dumpCols( self ):
		"Dumps out column structure"
		pprint( self.cols )

class table:
	def __init__( self, db, tdef ):
		self.db = db
		self.tdef = tdef
		#self.name = self.tdef.cols.name
		print "table instantiated with",self.tdef
		self.createTables([self.tdef.cols])
	def createTables(self, cols, name=''):
		for c in cols:
			print "%s col: %s" % (name, c)
			if type(c) == types.TupleType:
				tname, tbits = c
				print "%s bits: %s" % (tname, `tbits`)
				return self.createTables(tbits, '%s_%s' % (name, tname))
	def getName( self ):
		return self.tdef.cols[0]
	def __len__( self ):
		return self.db.selectScalar( 'SELECT COUNT(*) FROM %s' % ( self.getName(), ) )

class storage:
	def __init__( self, **kwArgs ):
		print "connect to database"
		self.db = apply( MySQLdb.connect, [], kwArgs )
	def getas( self, desc ):
		print "set up table: " + desc
		return table( self, tabledef( desc ) )
	def selectScalar( self, sql ):
		c = self.db.cursor()
		c.execute( sql )
		return c.fetchall()[0]
	def dump( self ):
		print "fetch tables"
		c = self.db.cursor()
		c.execute( 'SHOW TABLES' )
		for row in c.fetchall():
			print row

# Unit tests
if __name__ == '__main__':
	print "MyMetakit: test"
	
	if not os.path.isfile( 'local_auth.txt' ):
		print """You need to create a file called local_auth.txt which looks like this:

host='localhost'	<-- or your database server
user='test'		<-- or your database username
password='password'	<-- insert password here
database='test'		<-- name of your test table

Once done, create a database called 'test' on the MySQL server and give the specified test user full access to it:

mysql -u root -p
<enter your password>
CREATE DATABASE test;
use mysql;
INSERT INTO user ( Host, User, Password ) VALUES ( 'localhost', 'test', PASSWORD( 'password' ) );
GRANT ALL ON test TO test;
FLUSH PRIVILEGES;

Now you can run this script successfully.
"""

	execfile( 'local_auth.txt' )
	
	db = storage( host=host, user=user, passwd=password, db=database )
	db.dump()
	test = db.getas( 'test[name:S,addr[line:S],tel:S,age:I]' )
	test.tdef.dumpCols()
	print len( test )

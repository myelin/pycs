#!/usr/bin/env python

# Return rescued data to database form: rescued/settings.txt -> rescued/settings.dat
# Copyright (C) 2002 Phillip Pearson; MIT license (see other PyCS files)

import os,os.path,metakit,sys

print "open"
outdir = 'rescued'
if not os.path.isdir(outdir):
	os.mkdir(outdir)
import pycs_settings
pycs_settings.pycs_paths.DATADIR = pycs_settings.pycs_paths.CONFDIR = outdir
set = pycs_settings.Settings()
db = set.db
db.autocommit()
set.comments = set.db.getas(
        'comments[user:S,paragraph:S,notes[name:S,email:S,url:S,comment:S,date:S]]'
        ).ordered( 2 )

# read in all data
alldata = {}
execfile( 'rescued/settings.txt', alldata )
alldata = alldata['alldata']

def pushRowsIntoView( rows, view ):
	print "push rows into view"
	for row in rows:
		scalarKeys = {}
		viewKeys = {}
		#print "getting values from",row
		for key,val in row.items():
			if type(val) == type([]):
				viewKeys[key] = val
			else:
				scalarKeys[key] = val
		idx = view.append( scalarKeys )
		print "insert index",idx
		subview = view[idx]
		for key,val in viewKeys.items():
			#print "key",key,"val",val
			#print "subview.",key,"..."
			pushRowsIntoView( val, getattr( subview, key ) )

# pycs_settings.Settings.__init__ creates a row in set.meta that we
# don't want because we are about to restore one from the old
# database.

del set.meta[0]

# Now run through all the tables and put them back into the DB

for table in ( 'users', 'meta', 'comments' ):
	print "table",table
	data = alldata[table]
	v = getattr( set, table )
	l = len( v )
	print "currently",l,"rows in table"
	assert( l == 0 )
	pushRowsIntoView( data, v )

print "Commit to disk ..."
db.commit()

print "All done!  Now you can copy rescued/settings.dat to /var/lib/pycs/data/, cross your fingers, and start the server again!  Make a copy of your old /var/lib/pycs/data/settings.dat first though, just in case something hasn't worked."

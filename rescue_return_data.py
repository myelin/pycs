#!/usr/bin/env python

# Return rescued data to database form: settings.txt -> rescued.db

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
execfile( 'settings.txt', alldata )
alldata = alldata['alldata']

def massage( row ):
	for key,val in row.items():
		if type(val)==type([]):
			v = metakit.view()
			vsize = len( v )
			assert( vsize == 0 )
			for subrow in val:
				print "fix subrow",subrow
				fixed = massage(subrow)
				print "fixed up:",fixed
				v.append( fixed )
				vsize += 1
				assert( vsize == len( v ) )
			row[key] = v
	return row

for table in ( 'users', 'meta', 'comments' ):
	print "table",table
	data = alldata[table]
	v = getattr( set, table )
	l = len( v )
	print "currently",l,"rows in table"
	for row in data:
		print "add row to",table
		v.append( massage( row ) )
		l += 1
		if not ( l == len( v ) ):
			print "warning: expected",l,"rows, got",len(v)

print "commit"
db.commit()
print dir(db)
print "all done!"

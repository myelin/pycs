#!/usr/bin/env python

# Rescue data from a broken database (e.g. one which takes forever to
# open the weblogUpdates table)

# Read from rescued/settings.dat and save as rescued/settings.txt

# Copyright (C) 2002 Phillip Pearson; MIT license (see other PyCS
# files)

# To save a broken database file, stop the PyCS server, then copy your
# settings.dat file into rescued/settings.dat, run this script
# (rescue_data.py), then rename rescued/settings.dat and run
# rescue_return_data.py, which will create a new rescued/settings.dat.
# Copy that file into your /var/lib/pycs/data/ directory and start the
# server again.

# Good luck!

import os,metakit,sys

#print "copy"
#os.system( 'cp -v /var/lib/pycs/data/settings.dat ./settings.dat' )

print "open"
import pycs_settings
pycs_settings.pycs_paths.DATADIR = pycs_settings.pycs_paths.CONFDIR = 'rescued'
set = pycs_settings.Settings()
db = set.db
set.comments = set.db.getas(
        'comments[user:S,paragraph:S,notes[name:S,email:S,url:S,comment:S,date:S]]'
        ).ordered( 2 )

maxlines=0

def dumpview( v, indent='' ):
	rawrows = []
	print indent,"[dump",v,"]"
	global maxlines
	if maxlines:
		maxlines -= 1
		if maxlines == 0:
			raise "too many lines output"
	props = v.structure()
	#print indent,len(v),"rows"
	for row in v:
		values = {}
		#print indent,"[row]"
		for prop in props:
			#print "property",prop,dir(prop)
			data = getattr(row,prop.name)
			if prop.type == 'V':
				#print indent,prop.name
				values[prop.name] = dumpview(data,indent+"\t")
			else:
				#print indent,prop.name,prop.type,data
				values[prop.name] = data
		rawrows.append( values )
	return rawrows

output={}
for table in ( 'users', 'meta', 'comments' ):
	print "table",table
	v = getattr( set, table )
	output[table] = dumpview(v)
	import pprint
	so = sys.stdout
	try:
		sys.stdout = open( 'rescued/settings.txt', 'wt' )
		print "alldata = ("
		pprint.pprint( output )
		print ")"
	finally:
		sys.stdout.close()
		sys.stdout = so
		
	#print ":",metakit.dump(v)

print "All done!  This script might crash now if you have a dodgy database.  Don't worry about that - just hit Ctrl-C (or kill this process).  The data dump file has been saved so you can rebuild the database using rescue_return_data.py now."

#!/bin/sh

# this creates swish indexes for each user. It does full indexing, so you
# usually don't want to run it on servers with many users installed.

LIBDIR=$HOME/pycs/var/lib/pycs
ROOTDIR=$LIBDIR/www/users
SWISHDIR=$LIBDIR/swish++/

cd $ROOTDIR

for user in *
do
	echo Indexing user $user
	mkdir -p $SWISHDIR/$user
	pushd $SWISHDIR/$user
	index++ -e 'html:*.html' $ROOTDIR/$user
	popd
done

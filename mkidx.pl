#!/usr/bin/perl -w

# Python Community Server
#
#     mkidx.pl: Generator for www/users/index.html
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

use strict;

my $webDir = '/var/lib/pycs/www';

my @dirs = `ls $webDir/users/`;

open IDX, ">$webDir/users/index.html";

print IDX <<HTML;
<html>
<head>
 <title>Python Community Server:User dirs</title>
 <link rel="stylesheet" href="http://myelin.pycs.net/myelin.css" type="text/css" />
</head>
<body>
 <div class="maintitle"><strong>PyCS</strong>: User directories</div>
 <div class="homelink">[<a href="/">back</a>]</div>
<p>This is a raw listing of the ID codes of all the weblogs stored on this server.
Don't worry if it makes no sense - it's going to be replaced by something better
sometime.  The <a href="/system/updates.py">list of recently-updated weblogs</a>
would probably be more useful at the moment.  Also try the <a href="/">server
home page</a> for a more readable introduction to what's going on here!</p>
<ul>
HTML
for my $dir (@dirs) {
	chomp $dir;
	if ( $dir =~ /^(\d+)$/ ) {
		print IDX <<HTML;
<li><a href="$dir/">User $dir</a></li>
HTML
	}
}

print IDX <<HTML;
</ul>
</body>
</html>
HTML

close IDX;

#!/usr/bin/perl -w
use strict;

print <<HTML;
<html>
<head>
	<title>Python Community Server README</title>
</head>
<body style="background-color: lightgreen;">
<div style="margin-top: 0px; border: solid; border-color: green; background-color: white; padding-left: 3em; align: center; font-size: 1em;"><pre>
HTML

while (<>) {
    s|(http://[^\s]+)|<a href="$1">$1</a>|;
    print;
}

print <<HTML;
</pre></div>
</body>
</html>
HTML

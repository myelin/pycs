All Your RSS ...
============

A miniature aggregator, for the Python Community Server.

To use, edit update.py and put in the URL of your own community
server.  Now run update.py and gen.py regularly until it 'settles'.

  (Whenever it sees a new blog, it will drop all the entries from that
  blog on the top of the aggregated list, so they will blow away
  everything else there ... so if you already have a server full of
  blogs, there will be a period of instability while you wait for
  everyone to get picked up by the aggregator).

Now publicise the URL of the aggregator page ;-)

You can probably do the same thing with Spycyroll, but I was bored and
felt like reinventing the wheel.  This will work even if people don't
put <pubDate> elements into their RSS.

- Phillip Pearson; http://www.myelin.co.nz/phil/email.php

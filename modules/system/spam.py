#!/usr/bin/python

# Python Community Server
#
#     spam.py: Spam deletion admin function
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


import re
import default_handler
import metakit
import StringIO
import urllib
import string
import cgi
import binascii
import base64
import time
import strptime
import html_cleaner
import comments
import md5
import BeautifulSoup
db = set.pdb

[path, params, query, fragment] = request.split_uri()

# see if someone is logged in already
loggedInUser = None
headers = util.IndexHeaders( request )
cookies = util.IndexCookies( headers )
if cookies.has_key( 'userInfo' ):
	import re
	import binascii
	cookieU, cookieP = re.search( '"(.*?)_(.*?)"', cookies['userInfo'] ).groups()
	cookieU = binascii.unhexlify( cookieU )
	try:
		loggedInUser = set.FindUser( cookieU, cookieP )
	except set.PasswordIncorrect:
		pass

# Decode information in query string and form		
query = util.SplitQuery( query )
form = util.SplitQuery( input_data.read() )

s = []
add = s.append
add("""<pre><b>comment spam administration</b>\n""")

def menu():
	add('\n(<a href="spam.py">main</a> | <a href="spam.py?op=blanks">find blank comments</a> | <a href="spam.py?op=words">word analysis</a> | <a href="spam.py?op=search">search</a>)\n\n')

def list_all_comments():
	r = 0
	for usernum,postid,count in db.execute("SELECT usernum,postid,COUNT(id) FROM pycs_comments GROUP BY usernum,postid"):
		r += 1
		add("  %d/%s: %d\n" % (usernum, postid, count))
	add("(%d rows)\n" % r)

def list_all_people():
	for name,count in db.execute("SELECT postername,COUNT(id) AS ct FROM pycs_comments WHERE is_spam=0 GROUP BY postername ORDER BY ct DESC"):
		add('  %s posted <a href="spam.py?op=personsearch&name=%s">%d comments</a>\n' % (name, urllib.quote(name), count))

def personsearch(term, showspam):
	add("searching for %s ... " % term)
	showsp_msg = showspam and "don't " or ""
	add('(<a href="spam.py?op=markspam&name=%s">mark all as spam</a> | <a href="spam.py?op=personsearch&name=%s&showspam=%d">%sshow spam from this person</a>)\n\n' % (urllib.quote(term), urllib.quote(term), (not showspam and 1 or 0), showsp_msg))
	search("postername=%s", (term,), showspam=showspam)

def search(where, sqlargs, showspam=0):
	where += " AND is_spam=%d" % (showspam and 1 or 0)
	for cid,usernum,postid,postlink,postername,cmt in db.execute("SELECT id,usernum,postid,postlink,postername,commenttext FROM pycs_comments WHERE %s ORDER BY commentdate" % where, sqlargs):
		if postlink:
			post = ' (<a href="%s">post</a>)' % postlink
		else:
			post = ''
		add('%d/<a href="comments.py?u=%d&p=%s">%s</a>%s [<a href="spam.py?op=personsearch&name=%s">%s</a>] %s <a href="spam.py?op=setspam&id=%d&spam=%d">toggle</a>\n' % (usernum, usernum, postid, postid, post, urllib.quote(postername), util.esc(postername), util.esc(cmt[:100]), cid, ((not showspam))))

def analyse_words():
	add("word (link?) analysis...\n")
	links = {}
	for cmt, in db.execute("SELECT commenttext FROM pycs_comments WHERE commentdate > NOW() - interval '7 day'"):
#		add("<li>%s</li>" % util.esc(cmt[:100]))
		soup = BeautifulSoup.BeautifulSoup()
		soup.feed(cmt)
		atags = soup('a')
		for a in atags:
			for k,v in a.attrs:
				if k == 'href':
#					add("<li>%s</li>" % v)
					links[v] = links.get(v, 0) + 1
	links = [(v,k) for k,v in links.items()]
	links.sort()
	links.reverse()
	for count, link in links:
		add("<li>%d - %s</li>" % (count, link))
			
		
		
def main():
	count, = db.fetchone("SELECT COUNT(*) FROM pycs_comments")
	spamcount, = db.fetchone("SELECT COUNT(*) FROM pycs_comments WHERE is_spam=1")
	add("total: %d comments, %d marked as spam\n" % (count, spamcount))

	menu()

	op = query.get("op")
	showspam = int(query.get("showspam", 0))

	if op == 'personsearch':
		personsearch(query['name'], showspam)
	elif op == 'markspam':
		db.execute("UPDATE pycs_comments SET is_spam=1 WHERE postername=%s", (query['name'],))
		add("all marked as spam from %s\n" % util.esc(query['name']))
	elif op == 'blanks':
		count, = db.fetchone("SELECT COUNT(*) FROM pycs_comments WHERE commenttext=''")
		add("%d empty comments in db...\n" % count)
	#	db.execute("DELETE FROM pycs_comments WHERE commenttext=''")
	elif op == 'words':
		analyse_words()
	elif op == 'search':
		add("content search...\n")
		term = query.get("term") or 'viagra'
		add('<form method="GET"><input type="hidden" name="op" value="search"><input type="text" name="term" size="40" value="%s"><input type="submit" value="search"></form>\n' % term)
		search("commenttext LIKE '%%%s%%'" % db.rawquote(term), None)
	elif op == 'setspam':
		add("setting spam flag for a comment...\n")
		db.execute("UPDATE pycs_comments SET is_spam=%d WHERE id=%d", (int(query['spam']), int(query['id'])))
	else:
		list_all_people()

	menu()

if not loggedInUser or int( loggedInUser.usernum ) != int( set.conf['adminusernum'] ):
	add('\nyou probably want to <a href="login.py?return=%s">log in first</a> (you need to be an admin to use this page).\n' % urllib.quote(request.uri))
else:
	main()

add("</pre>")
request['Content-Type'] = 'text/html'
request.push(s)
request.done()

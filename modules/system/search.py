# Python Community Server
#
#     search.py: search your posts (in the mirroredPosts table)
#
# Copyright (c) 2003, Phillip Pearson <pp@myelin.co.nz>
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

import md5
import re
import cgi
import os
import sys
import binascii
import base64
import urllib

from html_cleaner import cleanHtml

# See pycs_module_handler.py for info on how modules work

# We should be able to get at the following globals:

#	request: an http request object
#		try request.split_uri() to get some info about the request


[path, params, query, fragment] = request.split_uri()
query = util.SplitQuery( query )
form = util.SplitQuery( input_data.read() )

request['Content-Type'] = 'text/html; charset=utf-8'

page = {
	'title': _('Search results'),
	'body': """<p>Something went wrong; there should be some text here!</p>
		<p>Mail <a href="mailto:pp@myelin.co.nz">Phil</a> at 
		<a href="http://www.myelin.co.nz/">Myelin</a> if you
		think something is broken.</p>""",
	}

# Actually generate the output

s = ""

def esc(s):
	return cgi.escape(s, 1)

AUTHORIZATION = re.compile (
		#			   scheme  challenge
		'Authorization: ([^ ]+) (.*)',
		re.IGNORECASE
		)

def get_matching_header(head_reg, headers):
	for line in headers:
		m = head_reg.match (line)
		if m and m.end() == len(line):
			return m.groups()

def auth_info():
	# find auth info
	m = get_matching_header(AUTHORIZATION, request.header)
	if m:
		scheme, challenge = m
		scheme = string.lower (scheme)
		if scheme == 'basic':
			cookie = challenge
			try:
				decoded = base64.decodestring (cookie)
			except binascii.error:
				print 'malformed authorization info <%s>' % cookie
				return None
			return string.split (decoded, ':')
		else:
			print 'unknown/unsupported auth method: %s' % scheme
			return None
	else:
		return None

ai = auth_info()
# <path>;<params>?<query>#<fragment>
path_regex = re.compile(
    #      path      params    query   fragment
        r'([^;?#]*)(;[^?#]*)?(\?[^#]*)?(#.*)?'
		)

def split_uri(uri):
	m = path_regex.match(uri)
	if not m or (m.end() != len(uri)):
		raise ValueError, "Broken URI"
	else:
		return m.groups()

def split_url(url):
	if url.startswith('http://'):
		firstslash = url.find('/', 7)
		if firstslash == -1:
			return split_uri('/')
		else:
			return split_uri(url[firstslash:])

def authorize(url):
	# rewrite url so we get something the authorizer can handle
	#print "auth for url:",url
	url = set.rewrite_h.rewriteUrl(url, quiet=1)
	#print "rewritten to:",url
	# split it up and authorize
	try:
		[path, params, query, fragment] = split_url(url)
	except ValueError:
		return 0
	return set.authorizer.authorize(path, query, ai, quiet=1)

URLUSER = re.compile(r'/users/(\d+)(/.*)$')

def webauthorize(url):
	url = set.rewrite_h.rewriteUrl(url, quiet=1)
	upm = URLUSER.match(url)
	auth_info = ()
	if ai:
		auth_info = ai
	if upm:
		if set.ar_h.checkUrlAccess(upm.group(1), upm.group(2), auth_info[0], auth_info[1]) == 0:
			return 0
	return 1
	
def allow_url_p(url):
	"url exclusion callback; checks a url and returns 1 if it should show in the search results"
	if webauthorize(url) == 0:
		return 0
	if set.authorizer is not None:
		# we've got an authorizer; refuse access to the file if the current
		# auth settings won't let the user see it.
		#print "we've got an authorizer"
		try:
			if not authorize(url):
				#print "it didn't like it!"
				return 0
		except:
			print "exception trying to run authorizer:"
			import traceback
			traceback.print_exc()
	# authentication turned off or the current user has permission to see the
	# url.  now check to see if it's a silly url that we don't want to show anyway
	# (rss.xml, mailto pages, etc).
	if (#not url.startswith('http://www.pycs.net')
	    url.endswith('.xml') or url.endswith('.opml')
	    or (url.find('/system/mailto.py?') != -1)
	    or url.endswith('/system/login.py')
	    or url.endswith('&format=rss')):
		return 0
	return 1

class Skip(Exception):
	"raise this to disqualify a post when searching"

def search(usernum, posts_t, query, skip_hits):
	"search the database for various words.  we don't do phrase searching - anybody want to hack it in?"
	words = query.lower().split()
	required = [] # if any required word is missing from a post, it won't show in the results
	excluded = [] # or if any excluded words are present, it won't show either
	nice = [] # if all required and no excluded words are there, 'nice' words help the ranking
	for word in words:
		if word.startswith('+'):
			required.append(word[1:])
		elif word.startswith('-'):
			excluded.append(word[1:])
		else:
			nice.append(word)
	ret = []
	add = ret.append
	#add("<p>(search results for %s --> rq %s, ex %s, n %s)</p>" % (words,required,excluded,nice))
	hits = []
	hits_skipped = 0
	max_hits = 10
	total_hits = 0
	for post_idx in range(len(posts_t)-1, -1, -1):
		post = posts_t[post_idx]
		if not allow_url_p(post.url): continue
		try:
			# get the post text
			text = (post.title + post.description).decode('utf-8').lower()
			# see if it has any excluded words
			for word in excluded:
				if text.find(word) != -1: raise Skip()
			# make sure it has all required words
			for word in required:
				if text.find(word) == -1: raise Skip()
			# now count 'nice' words
			count = 0
			for word in nice:
				if text.find(word) != -1: count += 1
			if len(nice) and not count: raise Skip()
			# if we got this far, we have a positive search result
			if hits_skipped < skip_hits:
				hits_skipped += 1
			elif len(hits) < max_hits:
				hits.append(post)
			total_hits += 1
		except Skip:
			pass
	if not len(hits):
		add("<p>No posts found.</p>")
	else:
		first_hit = skip_hits
		last_hit = skip_hits + len(hits)
		extra_link = ' <a href="search.py?u=%s&q=%%s&skip=%%d">%%s</a>.' % usernum
		extra = ''
		if first_hit > 1:
			prev_avail = min(skip_hits, max_hits)
			extra += extra_link % (urllib.quote(query.encode(set.DocumentEncoding())), first_hit-prev_avail, _("Show previous %s").decode(set.DocumentEncoding()) % prev_avail)
		if last_hit < total_hits:
			extra += extra_link % (urllib.quote(query.encode(set.DocumentEncoding())), last_hit, _("Show next %d").decode(set.DocumentEncoding()) % min(max_hits, total_hits - last_hit))
		add(_("<p>Showing hits %d-%d out of of %d. %s</p>") % (
			skip_hits + 1,
			skip_hits + len(hits),
			total_hits,
			extra
			))
		lastdate = None
		for post in hits:
			hitdate = post.date[:8]
			if lastdate != hitdate:
				lastdate = hitdate
				add('<h2>%s-%s-%s</h2>' % (lastdate[:4], lastdate[4:6], lastdate[6:]))
			add('<div class="searchhit"><h3><a href="%s">%s</a></h3>' % (esc(post.url), esc(post.title)))
			desc = cleanHtml(post.description)
			if len(desc) > 400:
				desc = desc[:400]
				desc = cleanHtml(desc)
				desc += ' ...'
			add('<div class="searchpost">%s</div></div>' % desc)
	html = ''
	for block in ret:
		if type(block) == type(u''):
			html += block.encode('utf-8')
		else:
			html += block
	return html

def main():
	usernum = query.get('u', None)
	if usernum is None:
		return "No usernum specified!"
	usernum = '%07d' % int(usernum)

	idx = set.mirrored_posts.find(usernum=usernum)
	if idx == -1:
		return _("Usernum %s has not submitted any posts to be indexed (so you can't search his/her weblog yet).") % usernum
	posts_t = set.mirrored_posts[idx].posts
	#posts_t = posts_t.sortrev((posts_t.date,),(posts_t.date,))
	posts_t = posts_t.sort(posts_t.date)

	search_terms = query.get('q', query.get('words', ''))
	try:
		search_terms = search_terms.decode('utf-8')
	except:
		search_terms = search_terms.decode(set.DocumentEncoding())
	skip_hits = int(query.get('skip', '0'))

	ret = """<p>%s</p>

	<form method="GET">
	<input type="hidden" name="u" value="%s" />
	%s <input type="text" size="80" name="q" value="%s" />
	</form>""" % (
		_('Searching weblog for usernum <b>%s</b>:') % usernum,
		usernum, _('Search:'), esc(search_terms)
	)

	if type(ret) == type(u''):
		ret = ret.encode('utf-8')
	else:
		ret = ret.decode(set.DocumentEncoding()).encode('utf-8')

	if search_terms:
		ret += search(usernum, posts_t, search_terms, skip_hits)
	else:
		ret += _("<p>You can search a blog with multiple words. The search syntax is as follows: a posting matches if at least one normal search term is in the postings text or title. If you prepend a + to a search word, this word is required. If you prepend a - to a search word, this word is forbiddend. Words don't need to be full word - actually a simple substring match is done.<p><b>foo bar +baz -booz</b><p>The above search terms would search for all posts where either <b>foo</b> or <b>bar</b> is found, <b>baz</b> is allways found and <b>booz</b> is never found.").decode(set.DocumentEncoding()).encode('utf-8')

	return ret

page['body'] = main()
s = set.Render( page )

request['Content-Length'] = len(s)
request.push( s )
request.done()

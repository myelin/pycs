# read all data from metakit database

import sys
sys.path.insert(0, "..")
import pycs_settings

def export(writer):
    set = pycs_settings.Settings(quiet=1)
    cmts = set.getCommentTable()
    n_comments = n_posts = 0
    for post in cmts:
        #print post.user, post.paragraph, post.link
        n_posts += 1
        for cmt in post.notes:
            #print "\t",cmt.name, cmt.email, cmt.url, cmt.date
            writer.write_comment(usernum=post.user, postid=post.paragraph, posturl=post.link,
                                 name=cmt.name, email=cmt.email, url=cmt.url, date=cmt.date, text=cmt.comment)
            n_comments += 1
    print "sent %d comments over %d posts to writer" % (n_comments, n_posts)

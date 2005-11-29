from __future__ import generators
import psycopg
import time, sys, socket
import search_engines
import pycs_paths

DBE = psycopg.DatabaseError

try:
    UnicodeDecodeError
except NameError:
    UnicodeDecodeError = UnicodeError

def CursorIterator(cur):
    while 1:
        row = cur.fetchone()
        if not row: break
        yield row

def toutf8(s):
    try:
        s = s.decode("utf-8")
    except UnicodeDecodeError:
        s = s.decode("iso-8859-1")
    return s.encode("utf-8")

FMT_8601 = "%Y%m%dT%H:%M:%S"
def timeto8601(t):
    return time.strftime(FMT_8601, t)

def fix8601(ts):
    # takes in a possibly-bogus 8601 timestamp and returns a good one
    try:
        time.strptime(ts, FMT_8601)
    except ValueError:
        ts = time.strftime(FMT_8601) # use current timestamp...
    return ts

def pyto8601(ts, has_am=1, allow_empty=0):
    if allow_empty and not ts:
        # empty timestamp - return empty result
        return None

    # do we need to decode AM/PM?
    if has_am:
        fmt = '%Y-%m-%d %I:%M:%S %p'
    else:
        fmt = '%Y-%m-%d %H:%M:%S'

    # now let's give it a go...
    try:
        t = time.strptime(ts, fmt)
    except:
        print "Error decoding timestamp %s with format %s" % (`ts`, `fmt`)
        raise

    # if that worked, t is a python time object and timeto8601 will give us an ISO8601 represntation.
    return timeto8601(t)

class DB:
    def __init__(self, set, host, db, user, pwd, noupgrade=0):
        self.set = set
        self.dbhost = host
        self.dbname = db
        self.dbuser = user
        self.dbpass = pwd

        self.connect()

        if noupgrade:
            print "WARNING: not upgrading database schema.  Stuff might not work if you run this straight after a code update but before restarting PyCS."
        else:
            self.update_schema()

    def connect(self):
        print "Connecting to PostgreSQL database...",
        self.con = psycopg.connect("host=%s dbname=%s user=%s password=%s" % (self.dbhost, self.dbname, self.dbuser, self.dbpass))
        print "connected"

    def disconnect(self):
        if self.con:
            self.con.close()
            self.con = None

    def quote(self, s):
        return psycopg._fix_arg(s)

    def rawquote(self, s):
        return self.quote(s)[1:-1]

    def _execute(self, sql, args=None):
        if not self.con: self.connect()
        cur = self.con.cursor()
        try:
#            print "executing",sql,args
            cur.execute(sql, args)
#            print cur
#            print dir(cur)
#            print "autocommit:",cur.autocommit
#            print "done"
        except socket.error, e:
            print>>sys.stderr, "got socket.error",e.args
            self.connect()
            cur.execute(sql, args)
        return cur

    def execute(self, sql, args=None):
        return CursorIterator(self._execute(sql, args))

    def fetchone(self, sql, args=None):
        return self._execute(sql, args).fetchone()

    def get_db_version(self):
        self.db_id, = self.fetchone("SELECT db_id FROM pycs_meta")
        print "Database is at version %d" % self.db_id

    def set_db_version(self, newver):
        self.execute("UPDATE pycs_meta SET db_id=%d", (newver,))
        self.execute("COMMIT")
        self.get_db_version()

    def update_schema(self):
        storFn = pycs_paths.DATADIR + "/settings.dat"
        print "Connecting to MetaKit database in %s" % storFn
        import metakit
        mkdb = metakit.storage(storFn, 1)
        
        print "Updating PostgreSQL database schema"

        # See if the database is completely new
        try:
            self.fetchone("SELECT db_id FROM pycs_meta")
        except DBE, e:
            if e.args[0].find("does not exist") != -1:
                print "Creating pycs_meta table"
                self.execute("""CREATE TABLE pycs_meta (db_id INT)""")
                self.execute("INSERT INTO pycs_meta (db_id) VALUES (0)")
            else:
                raise
        self.get_db_version()

        # if version 0, need to create the referrers table
        if self.db_id < 1:
            # grab MK table
            referrers_table = mkdb.getas("referrers[time:S,usernum:S,group:S,referrer:S,count:I]").ordered(2)
            # set up PG
            print "Creating pycs_referrers table"
            self.execute("""CREATE TABLE pycs_referrers (id INT PRIMARY KEY, hit_time TIMESTAMP, usernum INT, usergroup VARCHAR(32), referrer VARCHAR(2048), hit_count INT, is_search_engine BOOLEAN, search_engine VARCHAR(32), search_term VARCHAR(1024))""")
            self.execute("""CREATE SEQUENCE pycs_referrers_id_seq""")
            self.execute("""CREATE INDEX pycs_referrers_user_index ON pycs_referrers (usernum, usergroup)""")
            # copy data over
            print "Copying referrer data (%d rows) into pycs_referrers table" % len(referrers_table)
            count = 0
            for row in referrers_table:
                if not (count % 1000):
                    print "\r%s" % count,
                try:
                    matched, term = search_engines.checkUrlForSearchEngine(row.referrer)
                    if term: term = toutf8(term)
                    self.execute("INSERT INTO pycs_referrers (id, hit_time, usernum, usergroup, referrer, hit_count, is_search_engine, search_engine, search_term) VALUES (NEXTVAL('pycs_referrers_id_seq'), %s, %d, %s, %s, %d, %s, %s, %s)", (pyto8601(row.time), int(row.usernum), row.group, toutf8(row.referrer), row.count, (matched and term) and 't' or 'f', matched, term))
                except DBE, e:
                    print e
                    print (row.time, row.usernum, row.group, row.referrer, row.count)
                    raise
                count += 1
            print
            self.set_db_version(1)

        if self.db_id  < 2:
            comments_table = mkdb.getas('comments[user:S,paragraph:S,link:S,notes[name:S,email:S,url:S,comment:S,date:S]]').ordered( 2 )
            
            print "Creating pycs_comments table"
            #self.execute("""DROP TABLE pycs_comments""")
            #self.execute("""DROP SEQUENCE pycs_comments_id_seq""")
            self.execute("""CREATE TABLE pycs_comments (id INT PRIMARY KEY, usernum INT, postid VARCHAR(255), postlink VARCHAR(2048), commentdate TIMESTAMP, postername VARCHAR(255), posteremail VARCHAR(255), posterurl VARCHAR(2048), commenttext TEXT)""")
            self.execute("""CREATE SEQUENCE pycs_comments_id_seq""")
            self.execute("""CREATE INDEX pycs_comments_post_index ON pycs_comments (usernum, postid, id)""")
            print "Copying comments (for %d users) into pycs_comments table" % len(comments_table)
            for user_row in comments_table:
                usernum, postid, postlink = (user_row.user, user_row.paragraph, user_row.link)
                if not usernum:
                    usernum = 0
                else:
                    usernum = int(usernum)
                print "user %s post %s postlink %s: %d comments" % (`usernum`, `postid`, `postlink`, len(user_row.notes))
                for cmt_row in user_row.notes:
                    name, email, url, comment, date = (cmt_row.name, cmt_row.email, cmt_row.url, cmt_row.comment, cmt_row.date)
                    #print "name %s email %s url %s cmt %s... date %s" % (`name`, `email`, `url`, `comment[:20]`, date)
                    if date:
                        date = pyto8601(date, has_am=0)
                    else:
                        date = None
                    try:
                        self.execute("""INSERT INTO pycs_comments (id, usernum, postid, postlink, commentdate, postername, posteremail, posterurl, commenttext) VALUES (NEXTVAL('pycs_comments_id_seq'), %d, %s, %s, %s, %s, %s, %s, %s)""", (usernum, postid, postlink, date, toutf8(name), toutf8(email), toutf8(url), toutf8(comment)))
                    except:
                        print (usernum, postid, postlink, date, name, email, url, comment)
                        raise
            self.set_db_version(2)

        if self.db_id < 3:
            self.execute("""ALTER TABLE pycs_comments ADD COLUMN is_spam INT""")
            self.execute("""UPDATE pycs_comments SET is_spam=0""")
            self.set_db_version(3)

        if self.db_id < 4:
            self.execute("""DROP INDEX pycs_comments_post_index""")
            self.execute("""CREATE INDEX pycs_comments_post_index ON pycs_comments (is_spam, usernum, postid, id)""")
            self.set_db_version(4)

        if self.db_id < 5:
            # repair damage by comment bug that inserted NULL instead of 0 for is_spam on comment posting
            self.execute("""UPDATE pycs_comments SET is_spam=0 WHERE is_spam IS NULL""")
            self.set_db_version(5)

        if self.db_id < 6:
            print "Creating pycs_updates table for weblog updates"
            self.execute("""CREATE TABLE pycs_updates (update_time TIMESTAMP, url VARCHAR(1024), title VARCHAR(1024))""")
            self.execute("""CREATE INDEX pycs_updates_by_time ON pycs_updates (update_time)""")
            self.execute("""CREATE INDEX pycs_updates_url_title ON pycs_updates (url, title)""")

            # fill it with data
            print "Copying weblog update data over to pycs_updates table"
            updates_table = mkdb.getas('blogUpdates[updateTime:I,blogUrl:S,blogName:S]')
            for row in updates_table:
                self.execute("INSERT INTO pycs_updates (update_time, url, title) VALUES (%s, %s, %s)",
                             (timeto8601(time.localtime(row.updateTime)),
                              row.blogUrl,
                              row.blogName,
                              ))
            self.set_db_version(6)

        if self.db_id < 7:
            print "Creating pycs_spam_commenters table"
            self.execute("""CREATE TABLE pycs_spam_commenters (name VARCHAR(1024))""")
            self.execute("""CREATE INDEX pycs_spam_commenters_name ON pycs_spam_commenters (name)""")
            self.set_db_version(7)

        if self.db_id < 8:
            self.execute("""CREATE TABLE pycs_good_commenters (name VARCHAR(1024))""")
            self.execute("""CREATE INDEX pycs_good_commenters_name ON pycs_good_commenters (name)""")
            self.set_db_version(8)

        if self.db_id < 9:
            print "Indexing poster names in comments table"
            self.execute("""CREATE INDEX pycs_comments_postername ON pycs_comments (postername)""")
            self.set_db_version(9)

        if self.db_id < 10:
            print "Moving meta table into postgres"
            meta_table = mkdb.getas("meta[nextUsernum:I]")
            if len(meta_table) == 0:
                nextUsernum = 1
            else:
                nextUsernum = meta_table[0].nextUsernum
            
            self.execute("""CREATE SEQUENCE pycs_users_id_seq START %d""",
                         (nextUsernum,))
            self.set_db_version(10)

        if self.db_id < 11:
            print "Creating pycs_users table"

            users_table = mkdb.getas(
                "users[usernum:S,email:S,password:S,name:S,weblogTitle:S,serialNumber:S,organization:S," +
                "flBehindFirewall:I,hitstoday:I,hitsyesterday:I,hitsalltime:I," +
                "membersince:S,lastping:S,pings:I,lastupstream:S,upstreams:I,lastdelete:S,deletes:I,bytesupstreamed:I," +
                "signons:I,signedon:I,lastsignon:S,lastsignoff:S,clientPort:I,disabled:I,alias:S,flManila:I,bytesused:I,stylesheet:S,commentsdisabled:I]"
                ).ordered()
            
            if self.fetchone("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='pycs_users'"):
                self.execute("DROP TABLE pycs_users")

            self.execute("""CREATE TABLE pycs_users (usernum INT NOT NULL PRIMARY KEY, email VARCHAR(1024) NOT NULL, password CHAR(32) NOT NULL, name VARCHAR(1024) NOT NULL, weblogTitle VARCHAR(1024) NOT NULL DEFAULT '', serialNumber VARCHAR(128) NOT NULL DEFAULT '', organization VARCHAR(1024) NOT NULL DEFAULT '', flBehindFirewall INT NOT NULL DEFAULT 0, hitstoday INT NOT NULL DEFAULT 0, hitsyesterday INT NOT NULL DEFAULT 0, hitsalltime INT NOT NULL DEFAULT 0, membersince TIMESTAMP, lastping TIMESTAMP, pings INT NOT NULL DEFAULT 0, lastupstream TIMESTAMP, upstreams INT NOT NULL DEFAULT 0, lastdelete TIMESTAMP, deletes INT NOT NULL DEFAULT 0, bytesupstreamed INT NOT NULL DEFAULT 0, signons INT NOT NULL DEFAULT 0, signedon INT NOT NULL DEFAULT 0, lastsignon TIMESTAMP, lastsignoff TIMESTAMP, clientPort INT NOT NULL DEFAULT 0, disabled INT NOT NULL DEFAULT 0, alias VARCHAR(256), flManila INT NOT NULL DEFAULT 0, bytesused INT NOT NULL DEFAULT 0, stylesheet VARCHAR(2048), commentsdisabled INT)""")

            for user in users_table:
                try:
                    usernum = int(user.usernum)
                except:
                    print "can't decode usernum %s for user %s" % (`user.usernum`, `user`)
                    continue
                print "Adding usernum %d (%s) to the database" % (usernum, user.name)
                self.execute("INSERT INTO pycs_users (usernum, email, password, name, weblogTitle, serialNumber, organization, flBehindFirewall, hitstoday, hitsyesterday, hitsalltime, membersince, lastping, pings, lastupstream, upstreams, lastdelete, deletes, bytesupstreamed, signons, signedon, lastsignon, lastsignoff, clientPort, disabled, alias, flManila, bytesused, stylesheet, commentsdisabled) VALUES (%d, %s, %s, %s, %s, %s, %s, %d, %d, %d, %d, %s, %s, %d, %s, %d, %s, %d, %d, %d, %d, %s, %s, %d, %d, %s, %d, %d, %s, %d)", (
                    usernum,
                    toutf8(user.email),
                    user.password,
                    toutf8(user.name),
                    toutf8(user.weblogTitle),
                    toutf8(user.serialNumber),
                    toutf8(user.organization),
                    user.flBehindFirewall,
                    user.hitstoday,
                    user.hitsyesterday,
                    user.hitsalltime,
                    pyto8601(user.membersince, has_am=1, allow_empty=1),
                    pyto8601(user.lastping, has_am=1, allow_empty=1),
                    user.pings,
                    pyto8601(user.lastupstream, has_am=1, allow_empty=1),
                    user.upstreams,
                    pyto8601(user.lastdelete, has_am=1, allow_empty=1),
                    user.deletes,
                    user.bytesupstreamed,
                    user.signons,
                    user.signedon,
                    pyto8601(user.lastsignon, has_am=1, allow_empty=1),
                    pyto8601(user.lastsignoff, has_am=1, allow_empty=1),
                    user.clientPort,
                    user.disabled,
                    toutf8(user.alias),
                    user.flManila,
                    user.bytesused,
                    toutf8(user.stylesheet),
                    user.commentsdisabled,
                    ))
                             
            self.set_db_version(11)


        if self.db_id < 12:
            print "Adding pycs_mirroredposts table"
            if self.fetchone("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='pycs_mirrored_posts'"):
                self.execute("DROP TABLE pycs_mirrored_posts")
                                
            self.execute("""CREATE TABLE pycs_mirrored_posts (usernum INT, postdate TIMESTAMP, postid VARCHAR(1024), postguid VARCHAR(1024), posturl VARCHAR(1024), posttitle VARCHAR(1024), postcontent TEXT)""")

            mirrored_posts = mkdb.getas("mirroredPosts[usernum:S,posts[date:S,postid:S,guid:S,url:S,title:S,description:S]]")
            for user_posts in mirrored_posts:
                usernum = int(user_posts.usernum)
                print "Adding posts for usernum %d" % usernum
                for post in user_posts.posts:
                    print "\t%s" % post.title
                    self.execute("""INSERT INTO pycs_mirrored_posts (usernum, postdate, postid, postguid, posturl, posttitle, postcontent) VALUES (%d, %s, %s, %s, %s, %s, %s)""", (
                        int(usernum),
                        fix8601(post.date), # already iso-8601 so we don't need to decode it
                        toutf8(post.postid),
                        toutf8(post.guid),
                        toutf8(post.url),
                        toutf8(post.title),
                        toutf8(post.description),
                        ))
            self.set_db_version(12)

        # first hack at getting access restrictions in there.  it's
        # all messed up though - done without thinking enough.  i'm
        # checking this in to cvs anyway just in case someone else
        # wants to fix it up for me :-)
        if 0 and self.db_id < 13:
            print "moving access restrictions into postgres..."

            self.execute("CREATE TABLE pycs_access_locations (blogid INT, locname VARCHAR(1024), regexp VARCHAR(1024), groupname VARCHAR(1024))")
            self.execute("CREATE TABLE pycs_access_groups (blogid INT, groupname VARCHAR(1024), username VARCHAR(1024))")
            self.execute("CREATE TABLE pycs_access_users (blogid INT, username VARCHAR(1024), password VARCHAR(1024))")

            ar_locations = mkdb.getas(
                "arlocations[blogid:S,locname:S,regexp:S,group[name:S]]"
		).ordered(2)
            for loc in ar_locations:
                for group in loc.group:
                    self.execute("INSERT INTO pycs_access_locations (blogid, locname, regexp, groupname) VALUES (%d, %s, %s, %s)",
                                 (int(loc.blogid),
                                  toutf8(loc.locname),
                                  toutf8(loc.regexp),
                                  toutf8(group.name),
                                  ))

            ar_groups = mkdb.getas(
                "argroups[blogid:S,name:S,user[name:S]]"
		).ordered(2)
            for group in ar_groups:
                for user in group.user:
                    self.execute("INSERT INTO pycs_access_groups (blogid, groupname, username) VALUES (%d, %s, %s)",
                                 (int(group.blogid),
                                  toutf8(group.name),
                                  toutf8(user.name),
                                  ))

            ar_users = mkdb.getas(
                "arusers[blogid:S,name:S,password:S]"
                ).ordered(2)
            for user in ar_users:
                self.execute("INSERT INTO pycs_access_users (blogid, username, password) VALUES (%d, %s, %s)",
                             (int(user.blogid),
                              toutf8(user.name),
                              toutf8(user.password),
                              ))
            self.set_db_version(13)

        # next db id: 14

# not doing this because we don't get the IP address from the front-end proxy anyway
#        if self.db_id < XXX:
#            print "Adding IP address field to comments table"
#            self.execute("""ALTER TABLE pycs_comments ADD COLUMN posterip VARCHAR(15)""")
        
        print "Finished updating schema"

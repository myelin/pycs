import bpgsql
import time, sys, socket
import search_engines

DBE = bpgsql.DatabaseError

try:
    UnicodeDecodeError
except NameError:
    UnicodeDecodeError = UnicodeError

def toutf8(s):
    try:
        s = s.decode("utf-8")
    except UnicodeDecodeError:
        s = s.decode("iso-8859-1")
    return s.encode("utf-8")

def timeto8601(t):
    return time.strftime("%Y%m%dT%H:%M:%S", t)

def pyto8601(ts, has_am=1):
    if has_am:
        fmt = '%Y-%m-%d %I:%M:%S %p'
    else:
        fmt = '%Y-%m-%d %H:%M:%S'
    t = time.strptime(ts, fmt)
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
        self.con = bpgsql.connect(host=self.dbhost, dbname=self.dbname, username=self.dbuser, password=self.dbpass)
        print "connected"

    def disconnect(self):
        if self.con:
            self.con.close()
            self.con = None

    def quote(self, s):
        return bpgsql._fix_arg(s)

    def rawquote(self, s):
        return self.quote(s)[1:-1]

    def execute(self, sql, args=None):
        if not self.con: self.connect()
        cur = self.con.cursor()
        try:
            cur.execute(sql, args)
        except socket.error, e:
            print>>sys.stderr, "got socket.error",e.args
            self.connect()
            cur.execute(sql, args)
        return cur

    def fetchone(self, sql, args=None):
        return self.execute(sql, args).fetchone()

    def get_db_version(self):
        self.db_id, = self.fetchone("SELECT db_id FROM pycs_meta")
        print "Database is at version %d" % self.db_id

    def set_db_version(self, newver):
        self.execute("UPDATE pycs_meta SET db_id=%d", (newver,))
        self.get_db_version()

    def update_schema(self):
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
            referrers_table = self.set.db.getas("referrers[time:S,usernum:S,group:S,referrer:S,count:I]").ordered(2)
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
            comments_table = self.set.db.getas('comments[user:S,paragraph:S,link:S,notes[name:S,email:S,url:S,comment:S,date:S]]').ordered( 2 )
            
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
            updates_table = self.set.db.getas('blogUpdates[updateTime:I,blogUrl:S,blogName:S]')
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
        
        print "Finished updating schema"

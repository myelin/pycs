import bpgsql
import time
import search_engines

DBE = bpgsql.DatabaseError

try:
    UnicodeDecodeError
except NameError:
    UnicodeDecodeError = UnicodeError

def fixupunicode(s):
    try:
        return s.decode("utf-8")
    except UnicodeDecodeError:
        return s.decode("iso-8859-1")

def pyto8601(ts):
    t = time.strptime(ts, '%Y-%m-%d %I:%M:%S %p')
    return time.strftime("%Y%m%dT%H:%M:%S", t)

class DB:
    def __init__(self, set, host, db, user, pwd):
        self.set = set
        self.dbhost = host
        self.dbname = db
        self.dbuser = user
        self.dbpass = pwd

        self.connect()

        self.update_schema()

    def connect(self):
        print "Connecting to PostgreSQL database"
        self.con = bpgsql.connect(host=self.dbhost, dbname=self.dbname, username=self.dbuser, password=self.dbpass)
        print "Connected"

    def execute(self, sql, args=None):
        cur = self.con.cursor()
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
        print "Updating PostgrSQL database schema"

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
        if self.db_id == 0:
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
                    if term: term = fixupunicode(term).encode("utf-8")
                    self.execute("INSERT INTO pycs_referrers (id, hit_time, usernum, usergroup, referrer, hit_count, is_search_engine, search_engine, search_term) VALUES (NEXTVAL('pycs_referrers_id_seq'), %s, %d, %s, %s, %d, %s, %s, %s)", (pyto8601(row.time), int(row.usernum), row.group, fixupunicode(row.referrer).encode("utf-8"), row.count, (matched and term) and 't' or 'f', matched, term))
                except DBE, e:
                    print e
                    print (row.time, row.usernum, row.group, row.referrer, row.count)
                    raise
                count += 1
            print
            self.set_db_version(1)

        print "Finished updating schema"

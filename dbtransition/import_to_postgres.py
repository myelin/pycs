# data to generate sql for a postgres db

from pyPgSQL import PgSQL, libpq

def pg_esc(x):
    if x is None:
        return "NULL"
    try:
        x.decode("utf-8")
    except UnicodeError:
        x = x.decode("iso-8859-1").encode("utf-8")
    return PgSQL.PgQuoteString(x)

# to set up database: as root ...
"""
ROLLBACK;
CREATE USER pycs WITH
    ENCRYPTED PASSWORD 'kj1h234876'
    CREATEDB;
"""
# as pycs ...
"""
CREATE DATABASE pycs WITH
    ENCODING='UNICODE';
"""
# as root ...
"""
ALTER USER pycs WITH
    NOCREATEDB;
"""

class writer:
    def __init__(self, output_fn):
        self.out = open(output_fn, "wt")

        print>>self.out, """
        ROLLBACK;

        DROP TABLE comments;

        CREATE TABLE comments (
        id INT NOT NULL PRIMARY KEY DEFAULT NEXTVAL('comments_id_seq'),
        usernum VARCHAR(32),
        postid VARCHAR(1024),
        posturl VARCHAR(1024),
        name VARCHAR(256),
        email VARCHAR(256),
        url VARCHAR(1024),
        posted TIMESTAMP,
        content VARCHAR
        );

        DROP SEQUENCE comments_id_seq;
        CREATE SEQUENCE comments_id_seq;
        SELECT SETVAL('comments_id_seq', 1);

        CREATE INDEX comments_page ON comments (usernum, postid, posted);

        """

    def __del__(self):
        print>>self.out, """
        SELECT COUNT(*) FROM comments;
        SELECT COUNT(posted) FROM comments GROUP BY (usernum, postid);
        COMMIT;
        """
        
    def write_comment(self, usernum, postid, posturl, name, email, url, date, text):
        if not date:
            date = None
        sql = "INSERT INTO comments (usernum, postid, posturl, name, email, url, posted, content) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);" % tuple([pg_esc(x) for x in (usernum, postid, posturl, name, email, url, date, text)])
        print>>self.out, sql

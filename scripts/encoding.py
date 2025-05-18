import sys
print(sys.getdefaultencoding())

import psycopg2

conn = psycopg2.connect(
    dbname='rpacs',
    user='postgres',
    password='postgres',
    host='127.0.0.1',
    port=5432
)

cur = conn.cursor()
cur.execute("SHOW SERVER_ENCODING;")
print("SERVER_ENCODING:", cur.fetchone()[0])

cur.execute("SHOW CLIENT_ENCODING;")
print("CLIENT_ENCODING:", cur.fetchone()[0])

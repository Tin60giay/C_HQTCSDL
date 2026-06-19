import sys
sys.stdout.reconfigure(encoding='utf-8')
import pyodbc

conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost\\SQLEXPRESS;DATABASE=QLDSV_HTC;Trusted_Connection=yes;', autocommit=True)
cursor = conn.cursor()
cursor.execute("SELECT * FROM LOPTINCHI WHERE MALTC = 14")
cols = [c[0] for c in cursor.description]
print(dict(zip(cols, cursor.fetchone())))
conn.close()

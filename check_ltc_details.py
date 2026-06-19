import sys
sys.stdout.reconfigure(encoding='utf-8')
import pyodbc

conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost\\SQLEXPRESS;DATABASE=QLDSV_HTC;Trusted_Connection=yes;', autocommit=True)
cursor = conn.cursor()
cursor.execute("SELECT * FROM LOPTINCHI WHERE MAMH = 'CTDL'")
cols = [c[0] for c in cursor.description]
print("LOPTINCHI for CTDL:")
for r in cursor.fetchall():
    print(dict(zip(cols, r)))

cursor.execute("SELECT * FROM DANGKY WHERE MALTC IN (9, 13)")
cols_dk = [c[0] for c in cursor.description]
print("\nDANGKY for MALTC 9, 13:")
for r in cursor.fetchall():
    print(dict(zip(cols_dk, r)))
conn.close()

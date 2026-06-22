import sys
sys.stdout.reconfigure(encoding='utf-8')
import pyodbc

conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost\\SQLEXPRESS;DATABASE=QLDSV_HTC;Trusted_Connection=yes;', autocommit=True)
cursor = conn.cursor()
cursor.execute("SELECT * FROM LOP WHERE MALOP = 'E23CQCE01N'")
print(cursor.fetchone())
conn.close()

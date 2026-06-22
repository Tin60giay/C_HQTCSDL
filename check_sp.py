import sys
sys.stdout.reconfigure(encoding='utf-8')
import pyodbc 
conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=QLDSV_HTC;UID=GV01;PWD=GV01')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sys.objects WHERE type = 'P'")
print([r[0] for r in cursor.fetchall()])

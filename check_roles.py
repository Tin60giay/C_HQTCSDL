import pyodbc
try:
    conn = pyodbc.connect('Driver={ODBC Driver 17 for SQL Server};Server=localhost\\SQLEXPRESS;Database=QLDSV_HTC;UID=sa;PWD=123')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sys.database_principals WHERE type = 'R'")
    roles = [row.name for row in cursor.fetchall()]
    print('ROLES:', roles)
except Exception as e:
    print('ERROR:', e)

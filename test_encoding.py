import pyodbc
conn = pyodbc.connect(r'DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost\SQLEXPRESS;DATABASE=QLDSV_HTC;Trusted_Connection=yes;')
cursor = conn.cursor()
cursor.execute("EXEC SP_THEM_LOPTINCHI '2021-2022', 4, 'M', 1, 'G', 'K', 1")
row = cursor.fetchone()
print(row[1])

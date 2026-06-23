import pyodbc
import re
import sys

# Configure stdout to support Vietnamese accents in Windows console
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

def apply_sql_file():
    conn_str = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=QLDSV_HTC;Trusted_Connection=yes;'
    try:
        conn = pyodbc.connect(conn_str)
        print("Connected successfully using Windows Authentication (sysadmin).")
    except Exception as e:
        print(f"Failed to connect using Windows Authentication: {e}")
        return

    cursor = conn.cursor()
    
    with open('setup_login.sql', 'r', encoding='utf-8') as f:
        content = f.read()

    # Split script into batches by 'GO' on its own line (case-insensitive)
    batches = re.split(r'^\s*GO\s*$', content, flags=re.IGNORECASE | re.MULTILINE)
    
    success_count = 0
    fail_count = 0
    
    for i, batch in enumerate(batches):
        batch = batch.strip()
        if not batch:
            continue
            
        try:
            cursor.execute(batch)
            # Fetch output messages if any (like PRINT statements)
            while cursor.nextset():
                pass
            conn.commit()
            success_count += 1
        except Exception as e:
            # Print first 200 chars of batch to locate error
            snippet = batch[:200].replace('\n', ' ')
            print(f"\n[ERROR] Batch #{i+1} failed. Snippet: {snippet}")
            print(f"Error detail: {e}")
            fail_count += 1
            
    conn.close()
    print(f"\nExecution finished: {success_count} batches succeeded, {fail_count} batches failed.")

if __name__ == '__main__':
    apply_sql_file()

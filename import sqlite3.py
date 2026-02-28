import sqlite3
conn = sqlite3.connect('rvce_fee.db')
conn.execute("DELETE FROM pending_fees")
conn.commit()
conn.close()
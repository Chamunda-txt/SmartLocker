import os
import mysql.connector
from mysql.connector import Error

try:
    connection = mysql.connector.connect(
        host=os.getenv("SMARTLOCKER_DB_HOST", "localhost"),
        port=int(os.getenv("SMARTLOCKER_DB_PORT", "3306")),
        user=os.getenv("SMARTLOCKER_DB_USER", "root"),
        password=os.getenv("SMARTLOCKER_DB_PASSWORD", ""),
        database="smartlocker",
        connection_timeout=5,
    )

    print("SUCCESS: Connected to SmartLocker database!")

    cursor = connection.cursor()
    cursor.execute("SHOW TABLES")

    print("Tables in smartlocker database:")
    for table in cursor.fetchall():
        print("-", table[0])

    cursor.close()
    connection.close()

except (Error, ValueError) as error:
    print("CONNECTION FAILED:", error)
"""SmartLocker - Digital Vault with MySQL"""

import os
import sys
import csv
import webbrowser
from datetime import datetime

import mysql.connector
from mysql.connector import Error


def connect_database():
    """Connect to the local SmartLocker database."""
    try:
        connection = mysql.connector.connect(
            host=os.getenv("SMARTLOCKER_DB_HOST", "localhost"),
            port=int(os.getenv("SMARTLOCKER_DB_PORT", "3306")),
            user=os.getenv("SMARTLOCKER_DB_USER", "root"),
            password=os.getenv("SMARTLOCKER_DB_PASSWORD", ""),
            database="smartlocker",
            connection_timeout=5,
        )

        print("Connected to MySQL successfully!\n")
        return connection

    except (Error, ValueError) as error:
        print(f"Database connection failed: {error}")
        print("Check your MySQL server, credentials, and database.")
        return None


def add_file(connection):
    name = input("Enter file name: ").strip()
    link = input("Enter Google Drive or website link: ").strip()

    if not name or not link:
        print("File name and link cannot be empty.\n")
        return

    protect = input("Password protect this file? (yes/no): ").strip().lower()

    password = None
    hint = None
    protected = False

    if protect == "yes":
        print("Note: This version stores passwords as plain text.")
        print("Do not use a real or reused password.")
        password = input("Enter password: ")

        if not password:
            print("Password cannot be empty.\n")
            return

        hint = input("Enter password hint (optional): ").strip() or None
        protected = True

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO files (name, link, password, hint, protected)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (name, link, password, hint, protected),
            )
        connection.commit()
        print("File added successfully!\n")

    except Error as error:
        connection.rollback()
        print(f"Could not add file: {error}\n")


def get_file(connection):
    name = input("Enter file name: ").strip()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT link, password, protected, hint FROM files WHERE name = %s",
                (name,),
            )
            results = cursor.fetchall()

        if not results:
            print("File not found!\n")
            return

        if len(results) > 1:
            print("Multiple files have this name. Please rename duplicates first.\n")
            return

        link, password, protected, hint = results[0]

        if protected:
            entered_password = input("Enter password: ")

            if entered_password != password:
                print("Incorrect password!")
                if hint:
                    print(f"Hint: {hint}")
                print()
                return

        print("Opening link...")
        opened = webbrowser.open(link)

        if not opened:
            print("The browser may not have opened the link.")

    except Error as error:
        print(f"Could not retrieve file: {error}\n")


def delete_file(connection):
    name = input("Enter file name to delete: ").strip()

    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM files WHERE name = %s", (name,))
            deleted = cursor.rowcount

        connection.commit()

        if deleted:
            print(f"Deleted {deleted} matching record(s).\n")
        else:
            print("File not found.\n")

    except Error as error:
        connection.rollback()
        print(f"Could not delete file: {error}\n")


def rename_file(connection):
    old_name = input("Enter current file name: ").strip()
    new_name = input("Enter new file name: ").strip()

    if not new_name:
        print("New name cannot be empty.\n")
        return

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM files WHERE name = %s",
                (old_name,),
            )
            count = cursor.fetchone()[0]

            if count == 0:
                print("File not found.\n")
                return

            if count > 1:
                print("Multiple records have this name. Rename them individually first.\n")
                return

            cursor.execute(
                "UPDATE files SET name = %s WHERE name = %s",
                (new_name, old_name),
            )

        connection.commit()
        print("File renamed successfully!\n")

    except Error as error:
        connection.rollback()
        print(f"Could not rename file: {error}\n")


def display_files(connection):
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT name, protected, date_added FROM files ORDER BY date_added DESC"
            )
            results = cursor.fetchall()

        if not results:
            print("No files stored yet.\n")
            return

        print("\nStored Files:")
        print("-" * 50)

        for name, protected, date_added in results:
            lock = "LOCKED" if protected else "UNLOCKED"
            print(f"{lock} | {name} | Added on: {date_added}")

        print()

    except Error as error:
        print(f"Could not display files: {error}\n")


def search_files(connection):
    keyword = input("Enter keyword to search: ").strip()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT name, protected FROM files WHERE name LIKE %s",
                ("%" + keyword + "%",),
            )
            results = cursor.fetchall()

        if not results:
            print("No matching files found.\n")
            return

        print("\nSearch Results:")
        for name, protected in results:
            lock = "LOCKED" if protected else "UNLOCKED"
            print(f"{lock} | {name}")

        print()

    except Error as error:
        print(f"Could not search files: {error}\n")


def export_data(connection):
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT name, link, protected, hint, date_added FROM files"
            )
            results = cursor.fetchall()

        if not results:
            print("No data to export.\n")
            return

        filename = (
            "SmartLocker_Backup_"
            + datetime.now().strftime("%Y%m%d_%H%M%S")
            + ".csv"
        )

        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["Name", "Link", "Protected", "Hint", "Date Added"])
            writer.writerows(results)

        print(f"Backup exported successfully as {filename}\n")

    except (Error, OSError) as error:
        print(f"Could not export backup: {error}\n")


def about():
    print("""
SMARTLOCKER - DIGITAL VAULT
----------------------------------------
A Python application for managing digital links.

Features:
- Add, retrieve, delete, and rename links
- Search and display saved links
- Optional password protection
- Record creation date and time
- Export data to CSV

Interface: Command-line
Technologies: Python and MySQL
Developed by: Chamunda S
----------------------------------------
""")


def main():
    print("SmartLocker - Starting up...")
    print("Connecting to MySQL...")

    connection = connect_database()

    if connection is None:
        sys.exit(1)

    try:
        while True:
            print("""
========== SMARTLOCKER ==========
[1] Add New File
[2] Get File
[3] Delete File
[4] Rename File
[5] Display All Files
[6] Search Files
[7] Export Backup
[8] About
[9] Exit
=================================
""")

            choice = input("Enter your choice: ").strip()

            if choice == "1":
                add_file(connection)
            elif choice == "2":
                get_file(connection)
            elif choice == "3":
                delete_file(connection)
            elif choice == "4":
                rename_file(connection)
            elif choice == "5":
                display_files(connection)
            elif choice == "6":
                search_files(connection)
            elif choice == "7":
                export_data(connection)
            elif choice == "8":
                about()
            elif choice == "9":
                print("Exiting SmartLocker. Goodbye!")
                break
            else:
                print("Invalid choice. Try again.\n")

    except (EOFError, KeyboardInterrupt):
        print("\nSmartLocker stopped.")

    finally:
        connection.close()
        print("Database connection closed.")


if __name__ == "__main__":
    main()
from ldap3 import Server, Connection, ALL
import pyodbc
import hashlib

# Define LDAP server information
ldap_server = 'ldap://DESKTOP-PTCD1S6:389'      # Replace with LDAP link
ldap_user = 'cn=Directory Manager'              # Replace with LDAP user
ldap_password = 'password'                      # Replace with LDAP pass

# Define SQL server information
sql_driver = '{SQL Server}'
sql_server = 'DESKTOP-PTCD1S6'                  #Replace with SQL Server link
sql_database = 'ldapScrape'                     #Replace with SQL Database name
sql_trusted_connection = 'True'

# Name of the table
table_name = "ldap_data"

def hash_entry(entry):
    """ Create a SHA-256 hash of the entry's attributes. """
    hasher = hashlib.sha256()
    for attr in entry.entry_attributes:
        if attr.lower() != 'dn':  # Exclude distinguished name
            value = str(entry[attr].value)
            hasher.update(value.encode('utf-8'))
    return hasher.hexdigest()

def get_sql_hashes(cursor):
    """ Retrieve all current hashes from SQL Server. """
    cursor.execute(f"SELECT uid, entryHash FROM {table_name}")
    return dict(cursor.fetchall())

def check_and_add_hash_column(cursor):
    """ Check if the entryHash column exists and add it if it doesn't. """
    try:
        cursor.execute(f"SELECT entryHash FROM {table_name} WHERE 1=0")  # Test query for column existence
    except pyodbc.ProgrammingError as e:
        if 'Invalid column name' in str(e):
            print("Adding 'entryHash' column to the table.")
            cursor.execute(f"ALTER TABLE {table_name} ADD entryHash VARCHAR(64)")
            cursor.commit()
        else:
            raise

def update_entry_in_sql(cursor, entry_dict, entry_hash):
    """ Update the SQL entry with new LDAP data. """
    columns = ', '.join(entry_dict.keys())
    update_placeholders = ', '.join(f"{col} = ?" for col in entry_dict)
    values = tuple(
        str(value) if value is not None else None
        for value in entry_dict.values()
    )

    # Construct the SQL UPDATE statement
    sql_update = f"""
    UPDATE {table_name}
    SET {update_placeholders}, entryHash = ?
    WHERE uid = ?;
    """
    # Append the entry hash and the UID to the values tuple for the SQL parameters
    parameters = values + (entry_hash, entry_dict['uid'])

    cursor.execute(sql_update, parameters)

def insert_entry_in_sql(cursor, entry_dict, entry_hash):
    """ Insert a new LDAP entry into SQL Server. """
    columns = ', '.join(entry_dict.keys())
    placeholders = ', '.join('?' for _ in entry_dict)
    values = tuple(
        str(value) if value is not None else None
        for value in entry_dict.values()
    )

    # Construct the SQL INSERT statement
    sql_insert = f"INSERT INTO {table_name} ({columns}, entryHash) VALUES ({placeholders}, ?)"
    # Append the entry hash to the values tuple for the SQL parameters
    parameters = values + (entry_hash,)

    cursor.execute(sql_insert, parameters)

def update_sql_from_ldap():
    server = Server(ldap_server, get_info=ALL)
    conn = Connection(server, ldap_user, ldap_password, auto_bind=True)

    search_filter = '(objectClass=person)'
    conn.search('ou=People,dc=example,dc=com', search_filter, attributes=['*'])

    sql_connection = pyodbc.connect(f'Driver={sql_driver};'
                                    f'Server={sql_server};'
                                    f'Database={sql_database};'
                                    f'Trusted_Connection={sql_trusted_connection};')
    cursor = sql_connection.cursor()
    
    # Check and add entryHash column if it doesn't exist
    check_and_add_hash_column(cursor)

    # Retrieve current hashes from SQL Server
    sql_hashes = get_sql_hashes(cursor)

    for entry in conn.entries:
        entry_dict = {attr: entry[attr].value for attr in entry.entry_attributes if attr.lower() != 'dn'}
        entry_hash = hash_entry(entry)

        if entry_dict['uid'] in sql_hashes:
            if sql_hashes[entry_dict['uid']] != entry_hash:
                # The entry has changed, update it in SQL Server
                update_entry_in_sql(cursor, entry_dict, entry_hash)
        else:
            # The entry is new, insert it in SQL Server
            insert_entry_in_sql(cursor, entry_dict, entry_hash)

    # Remove deleted entries
    ldap_uids = {entry['uid'].value for entry in conn.entries}
    sql_uids = set(sql_hashes.keys())
    deleted_uids = sql_uids - ldap_uids
    for uid in deleted_uids:
        cursor.execute(f"DELETE FROM {table_name} WHERE uid = ?", uid)

    # Commit the changes and close connections
    sql_connection.commit()
    cursor.close()
    sql_connection.close()
    conn.unbind()

if __name__ == "__main__":
    update_sql_from_ldap()
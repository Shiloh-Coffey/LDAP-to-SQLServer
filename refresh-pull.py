from ldap3 import Server, Connection, ALL
import pyodbc
import hashlib
import config  # Import the configuration

# Use variables from config
ldap_server = config.LDAP_SERVER
ldap_user = config.LDAP_USER
ldap_password = config.LDAP_PASSWORD
sql_driver = config.SQL_DRIVER
sql_server = config.SQL_SERVER
sql_database = config.SQL_DATABASE
sql_trusted_connection = config.SQL_TRUSTED_CONNECTION
table_name = config.TABLE_NAME
master_ou_list = config.MASTER_OU_LIST

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

def update_sql_from_ldap(ou_list):
    server = Server(ldap_server, get_info=ALL)
    conn = Connection(server, ldap_user, ldap_password, auto_bind=True)

    sql_connection = pyodbc.connect(f'Driver={sql_driver};'
                                    f'Server={sql_server};'
                                    f'Database={sql_database};'
                                    f'Trusted_Connection={sql_trusted_connection};')
    cursor = sql_connection.cursor()
    
    # Check and add entryHash column if it doesn't exist
    check_and_add_hash_column(cursor)

    # Retrieve current hashes from SQL Server
    sql_hashes = get_sql_hashes(cursor)

    ldap_uids = set()

    for ou in ou_list:
        search_base = f'ou={ou},{config.SEARCH_BASE}'  # Adjust the base DN as per your LDAP structure
        search_filter = config.OBJECT_CLASS
        conn.search(search_base, search_filter, attributes=['*'])

        for entry in conn.entries:
            entry_dict = {attr: entry[attr].value for attr in entry.entry_attributes if attr.lower() != 'dn'}
            entry_hash = hash_entry(entry)
            ldap_uids.add(entry_dict['uid'])

            if entry_dict['uid'] in sql_hashes:
                if sql_hashes[entry_dict['uid']] != entry_hash:
                    # The entry has changed, update it in SQL Server
                    update_entry_in_sql(cursor, entry_dict, entry_hash)
            else:
                # The entry is new, insert it in SQL Server
                insert_entry_in_sql(cursor, entry_dict, entry_hash)

    # Remove deleted entries
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
    update_sql_from_ldap(master_ou_list)
    print('Server Refresh Finished')
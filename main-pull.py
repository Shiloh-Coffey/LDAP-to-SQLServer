from ldap3 import Server, Connection, ALL
import pyodbc
import config  # Import the configuration

# Use variables from config
ldap_server = config.LDAP_SERVER
ldap_user = config.LDAP_USER
ldap_password = config.LDAP_PASSWORD
sql_driver = config.SQL_DRIVER
sql_server = config.SQL_SERVER
sql_database = config.SQL_DATABASE
sql_trusted_connection = config.SQL_TRUSTED_CONNECTION
new_table_name = config.NEW_TABLE_NAME
table_name = config.TABLE_NAME
old_table_name = config.OLD_TABLE_NAME
master_ou_list = config.MASTER_OU_LIST
OID_TO_SYNTAX = config.OID_TO_SYNTAX

def attributePull(ou_list):
    # Connect and bind to the server
    server = Server(ldap_server, get_info=ALL)
    conn = Connection(server, user=ldap_user, password=ldap_password, auto_bind=True)

    all_attributes = set()

    for ou in ou_list:
        # Define a broader search base for each OU
        search_base = f'ou={ou},{config.SEARCH_BASE}'
        search_filter = config.SEARCH_FILTER

        # Search for entries in each OU
        conn.search(search_base=search_base, search_filter=search_filter, attributes=['objectClass'], size_limit=1)

        # Check if an entry was returned
        if not conn.entries:
            print(f"No entries found in {ou}!")
            continue

        # Process the first entry
        entry = conn.entries[0]
        print(f"Processing entry for attributes in {ou}:", entry.entry_dn)

        # Get all objectClasses for the entry
        object_classes = entry['objectClass']

        # Retrieve all attributes for each objectClass from the schema
        for oc in object_classes:
            if oc in server.schema.object_classes:
                object_class_schema = server.schema.object_classes[oc]
                all_attributes.update(object_class_schema.must_contain)
                all_attributes.update(object_class_schema.may_contain)

    return all_attributes


def get_attribute_datatypes(server_url, bind_dn, password, attributes):
    # Connect to the server and bind
    server = Server(server_url, get_info=ALL)
    conn = Connection(server, bind_dn, password, auto_bind=True)

    # Fetch the LDAP schema
    schema = server.schema

    # Retrieve and save the datatype of each attribute to the list of lists
    attribute_datatypes_list = []
    for attr in attributes:
        datatype = None
        if attr in schema.attribute_types:
            oid = schema.attribute_types[attr].syntax
            datatype = OID_TO_SYNTAX.get(oid, 'varchar(max)')
        attribute_datatypes_list.append([attr, datatype])

    return attribute_datatypes_list

def return_datatypes():
    attributes_to_check = attributePull(master_ou_list)
    datatypes_list = get_attribute_datatypes(ldap_server, ldap_user, ldap_password, attributes_to_check)
    return datatypes_list
 
def bind(ou_list):
    # Create an LDAP connection
    server = Server(ldap_server, get_info=ALL)
    conn = Connection(server, ldap_user, ldap_password, auto_bind=True)

    # Initialize an empty list to hold the results
    all_entries = []

    for ou in ou_list:
        # Define the LDAP query and the base DN (Distinguished Name) to search
        search_base = f'ou={ou},{config.SEARCH_BASE}'  # Adjust the base DN as per your LDAP structure
        # Define Object Class that is on the personnel records
        search_filter = config.OBJECT_CLASS
        # Define what attributes to pull
        attributes = ['*']

        # Perform the LDAP search
        conn.search(search_base, search_filter, attributes=attributes)

        # Iterate through the search results
        for entry in conn.entries:
            # Create a dictionary for the current entry's attributes
            entry_dict = {}
            # Iterate through each attribute in the entry
            for attribute in entry.entry_attributes:
                # Skip the 'dn' attribute
                if attribute.lower() != 'dn':
                    # Assign the attribute and its value to the dictionary
                    entry_dict[attribute] = entry[attribute].value
            # Add the current entry's dictionary to the main list
            all_entries.append(entry_dict)

    # Close the LDAP connection
    conn.unbind()

    sql_connection = pyodbc.connect(f'Driver={sql_driver};'
                                 f'Server={sql_server};'
                                 f'Database={sql_database};'
                                 f'Trusted_Connection={sql_trusted_connection};')
    cursor = sql_connection.cursor()

    # Iterate over all LDAP entries
    for entry in all_entries:
        # Construct column names and values for the INSERT statement
        columns = ', '.join(entry.keys())
        placeholders = ', '.join('?' for _ in entry)  # Use placeholders for parameterized queries

        # Convert values to a tuple, ensuring all values are properly cast to SQL-compatible types
        values = tuple(
            str(value) if isinstance(value, (list, dict, set))  # Convert lists, dicts, and sets to string
            else value
            for value in entry.values()
        )

        # Construct the INSERT statement
        sql_insert_statement = f"INSERT INTO {new_table_name} ({columns}) VALUES ({placeholders})"

        try:
            # Execute the SQL INSERT statement
            cursor.execute(sql_insert_statement, values)
        except pyodbc.Error as e:
            print("An error occurred:", e)
            # Handle the error e.g., by logging it or by taking other appropriate actions

    # Commit the changes to the database
    sql_connection.commit()

    # Close the cursor and connection
    cursor.close()
    sql_connection.close()    

def main():

    connSql = pyodbc.connect(f'Driver={sql_driver};'
                             f'Server={sql_server};'
                             f'Database={sql_database};'
                             f'Trusted_Connection={sql_trusted_connection};')
    
    # Pulls all attributes that can be attached to a user
    user_attributes = return_datatypes()    
    column_definitions =[]
    for attr in user_attributes:
        column_definitions.append(f"{attr[0]} {attr[1]}")

    # Join column definitions to form the CREATE TABLE statement
    sql_create = f"CREATE TABLE {new_table_name} (\n\t" + ",\n\t".join(column_definitions) + "\n);"
    cursor = connSql.cursor()
    cursor.execute(sql_create)
    connSql.commit()
    bind(master_ou_list)
    
    #rename tables
    sql_rename = f"""
        IF OBJECT_ID('{table_name}', 'U') IS NOT NULL
        BEGIN
        BEGIN TRANSACTION
        exec sp_rename '{table_name}','{old_table_name}'
        exec sp_rename '{new_table_name}','{table_name}'
        COMMIT TRANSACTION
        END
        ELSE
        BEGIN
        BEGIN TRANSACTION
        exec sp_rename '{new_table_name}','{table_name}'
        COMMIT TRANSACTION
        END
        """
    cursor = connSql.cursor()
    cursor.execute(sql_rename)
    connSql.commit()
    
    #drop old table
    sql_delete = f"""
        IF OBJECT_ID('{old_table_name}', 'U') IS NOT NULL
        DROP TABLE {old_table_name};
        """
    cursor = connSql.cursor()
    cursor.execute(sql_delete)
    connSql.commit()
    
if __name__ == "__main__":
    main()
    print('Server Bind Finished')
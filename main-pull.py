from ldap3 import Server, Connection, ALL
import pyodbc

# Define LDAP server information
ldap_server = 'ldap://DESKTOP-PTCD1S6:389'      #Replace with LDAP link
ldap_user = 'cn=Directory Manager'              #Replace with LDAP user
ldap_password = 'password'                      #Replace with LDAP pass

# Define SQL server information
sql_driver = '{SQL Server}'                     
sql_server = 'DESKTOP-PTCD1S6'                  #Replace with SQL Server link
sql_database = 'ldapScrape'                     #Replace with SQL Database name
sql_trusted_connection = 'True'

# Name of the table to create
new_table_name = "staging_ldap_data"
table_name = "ldap_data"
old_table_name = "dated_ldap_data"

# OID translation to Syntax for things that are not strings in LDAP, add translations as needed
OID_TO_SYNTAX = {
    '1.3.6.1.4.1.1466.115.121.1.27': 'int',
    '1.3.6.1.4.1.1466.115.121.1.53': 'datetime',
}

# Checks to see if table exists in SQL Sever
def attributePull ():
    # Define a broader search base
    search_base = 'ou=People,dc=example,dc=com'
    search_filter = '(objectClass=inetOrgPerson)'  # Adjust filter as per your needs

    # Connect and bind to the server
    server = Server(ldap_server, get_info=ALL)
    conn = Connection(server, user=ldap_user, password=ldap_password, auto_bind=True)

    #Search for entries
    conn.search(search_base=search_base, search_filter=search_filter, attributes=['objectClass'], size_limit=1)

    # Check if an entry was returned
    if not conn.entries:
        print("No entries found!")
        exit(1)

    # Process the first entry
    entry = conn.entries[0]
    print("Processing entry for attributes:", entry.entry_dn)

    # Get all objectClasses for the entry
    object_classes = conn.entries[0]['objectClass']

    # Retrieve all attributes for each objectClass from the schema
    all_attributes = set()
    for oc in object_classes:
        if oc in server.schema.object_classes:
            object_class_schema = server.schema.object_classes[oc]
            all_attributes.update(object_class_schema.must_contain)
            all_attributes.update(object_class_schema.may_contain)
    return (all_attributes)

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
    attributes_to_check = attributePull()
    datatypes_list = get_attribute_datatypes(ldap_server, ldap_user, ldap_password, attributes_to_check)
    return datatypes_list
 
def bind():
    # Create an LDAP connection
    server = Server(ldap_server, get_info=ALL)
    conn = Connection(server, ldap_user, ldap_password, auto_bind=True)

    # Define the LDAP query and the base DN (Distinguished Name) to search
    search_base = 'ou=People,dc=example,dc=com'
    # Define Object Class that is on the personnel records
    search_filter = '(objectClass=person)'
    # Define what attributes to pull
    attributes = ['*']

    # Perform the LDAP search
    conn.search(search_base, search_filter, attributes=attributes)

    # Initialize an empty list to hold the results
    all_entries = []

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
    bind()
    
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
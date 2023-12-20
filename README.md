# LDAP-to-SQLServer
Both scripts are designed to automate the process of extracting data from an LDAP server and maintaining an up-to-date copy of this data in a SQL Server database. They are useful in scenarios where LDAP data needs to be regularly synchronized with a SQL database, such as for user management or directory services.

## main-pull.py
This script performs several key functions:

    LDAP Connection: It connects to an LDAP server using the ldap3 library. The connection details (server, user, password) are hardcoded and should be replaced with actual LDAP server details.
    
    SQL Server Connection: It connects to a SQL Server database using the pyodbc library. Similar to the LDAP connection, the details for the SQL Server are hardcoded.
    
    Data Handling: The script pulls data from the LDAP server and processes it. It includes functions to:
        Pull attributes from LDAP entries.
        Determine the data types of these attributes.
        Create a new table in the SQL Server database with these attributes.
        Insert LDAP data into the SQL Server database.
        
    Table Management: It handles SQL Server tables by creating new tables and renaming or dropping old ones as needed.

## refresh-pull.py
This script is designed to update the SQL Server database with the latest data from the LDAP server:

    LDAP and SQL Server Connections: Similar to main-pull.py, it establishes connections to both LDAP and SQL Server.
    
    Data Synchronization: The script checks for updates in the LDAP data and synchronizes these changes with the SQL Server database. It includes functions to:
        Hash LDAP entries to detect changes.
        Retrieve current data from SQL Server for comparison.
        Update or insert new data into the SQL Server database.
        Remove deleted entries from the SQL Server database.

## Build and run your Docker image
    Build your Docker image: 'docker build -t ldap-to-sql .'
    Test running your container: 'docker run --rm ldap-to-sql'

## Create a cron job for scheduling
Edit the crontab file by running crontab -e in your terminal.
Add the following lines to schedule the Docker containers:
    0 0 * * 0 docker run --rm ldap-to-sql python /usr/src/app/main-pull.py
    0 * * * * docker run --rm ldap-to-sql python /usr/src/app/refresh-pull.py
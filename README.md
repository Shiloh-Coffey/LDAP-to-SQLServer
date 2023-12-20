# LDAP-to-SQLServer
The repository contains scripts designed to automate the process of extracting data from an LDAP server and maintaining an up-to-date copy of this data in a SQL Server database. This is particularly useful for scenarios where LDAP data needs to be regularly synchronized with a SQL database, such as for user management or directory services.

## Repository Contents
main-pull.py: This script connects to an LDAP server and a SQL Server database, pulls data from LDAP, processes it, and then inserts it into the SQL Server database. It also handles table management in the SQL Server.

refresh-pull.py: This script updates the SQL Server database with the latest data from the LDAP server. It includes functions for data synchronization, such as detecting changes in LDAP entries and updating the SQL Server database accordingly.

config.py: Contains configuration settings for LDAP and SQL Server connections.
## How to Use
### Build and Run Docker Image:
Build the Docker image using 

    docker build -t ldap-to-sql .
Test running the container with 

    docker run --rm ldap-to-sql
### Create a Cron Job for Scheduling:
Edit the crontab file (crontab -e) to schedule the Docker containers:

    0 0 * * 0 docker run --rm ldap-to-sql python /usr/src/app/main-pull.py
    0 * * * * docker run --rm ldap-to-sql python /usr/src/app/refresh-pull.py

## Additional Information
The scripts use the ldap3 library for LDAP connections and the pyodbc library for SQL Server connections.

The main-pull.py script includes functions for pulling attributes from LDAP entries, determining data types, creating new tables, and inserting data into SQL Server.

The refresh-pull.py script synchronizes updates from LDAP to SQL Server, including hashing LDAP entries to detect changes and updating or inserting new data into SQL Server.

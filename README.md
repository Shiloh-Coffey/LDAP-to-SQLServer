# LDAP-to-SQLServer
Scapes data from an LDAP and injects in into a SQLServer database

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

Both scripts are designed to automate the process of extracting data from an LDAP server and maintaining an up-to-date copy of this data in a SQL Server database. They are useful in scenarios where LDAP data needs to be regularly synchronized with a SQL database, such as for user management or directory services.

## Roadmap
![Roadmap](https://mermaid.ink/svg/pako:eNp9U01vGjEQ_SsjS4hESiq1vfmGgANSSNNC1cteXHsAl13btcdpCeK_d2a30CYH5jQ7Ox_vPc8clY0OlVaj0dEHTxqOY9phh2M9dibvx6fTaNSEzgfXmdQEYMsx0s3NlOtgHnYmWE4PXPkwmzzdU7xffX5YYX7GDF8wxeIp5sPt7VArtjZlD-81TJwDzoVF-IGWfAzwlCMN7r9ssRkWm32SHxoWXWr7iZBMNh0SZv-CDn5WdrAARUgZnyVBuvtz93eve4qtyFAtGqZRehK-wfhBwxoL-bCFydb4UAjmw-gC650hqc8EMTMF21bW47F23zEXMIGpJbTetDDdMUzLKMsVUjMG3MbUF-YagHhuTwVDqRmB3wTkpYD1di2zZBA92yIQBOEvTzuBYmMgxiqh8B-a8heNvaAB3GxEGR58uKJNzxHdG2k-aliaPcKC4FvMe9jw5GVtybOO8ClvTfAvRqjxyK-8V9e4z38TMkKhuKnBDlWeDkK_1JQia9yde8fXvav05jful68namPOWFIMTiTo5RKHU2QbhsW8Qvcx0pmyulMd5s54x_dxlJJG9bfRKM2unEejmnDiPFMprg7BKk254p2qyRnCmTdb3lClN6Ytl-jcyUVcgth_Locr7I_x9Ad4CzGq)
CAO: 28NOV2023

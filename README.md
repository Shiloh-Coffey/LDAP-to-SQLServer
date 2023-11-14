# LDAP-to-SQLServer
Scapes data from an LDAP and injects in into a SQLServer database

# Main Pull
This script looks for all attributes with a given Organizational Unit and creates a SQL table with the attributes as columns.
It then adds all the given Organizational Unit entries as rows in the table.
It saves all of this into a temp table and then renames it to the active table to minimize downtime.

# Refresh Pull
This script generates a hash of all columns for all rows and places this hash in a new column. 
It then compares the hash of all attributes in the SQL Table to the given LDAP to see if changes have been made.
It then updates the SQL Table on which entries have changes noted in the generated hash.

# LDAP server information
LDAP_SERVER = 'ldap://DESKTOP-KJ24FOM:389'
LDAP_USER = 'cn=Directory Manager'
LDAP_PASSWORD = 'password'

# SQL server information
SQL_DRIVER = '{SQL Server}'
SQL_SERVER = 'DESKTOP-KJ24FOM'
SQL_DATABASE = 'ldapScrape'
SQL_TRUSTED_CONNECTION = 'True'

# Table names
NEW_TABLE_NAME = "staging_ldap_data"
TABLE_NAME = "ldap_data"
OLD_TABLE_NAME = "dated_ldap_data"

# List of OUs to search
MASTER_OU_LIST = ['People', 'Security']

# OID translation to Syntax for things that are not strings in LDAP
OID_TO_SYNTAX = {
    '1.3.6.1.4.1.1466.115.121.1.27': 'int',
    '1.3.6.1.4.1.1466.115.121.1.53': 'datetime',
}

# Search filter
SEARCH_BASE = 'dc=example,dc=com'
SEARCH_FILTER = '(objectClass=inetOrgPerson)'

# Object class for LDAP search
OBJECT_CLASS = '(objectClass=person)'
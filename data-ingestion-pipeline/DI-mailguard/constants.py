from decouple import config

EMAIL_USER = config("EMAIL_UNAME")
EMAIL_PWD = config("EMAIL_PWD")
CONN_STR = config("BLOB_CONN_STR")
BLOB_NAME = "<your bucket Name>"
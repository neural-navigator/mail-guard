from azure.functions import HttpRequest, HttpResponse, Out
import logging
import os

import imaplib
import email
import json
import logging
from azure.storage.blob import BlobServiceClient
from datetime import datetime
from . import constants
from .ingest_email import GmailReader


def main(req: HttpRequest, outputBlob: Out[bytes]) -> HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    try:
        # Initialize GmailReader
        gmail_reader = GmailReader(
            email_user=constants.EMAIL_USER,
            email_pass=constants.EMAIL_PWD,
            azure_conn_str=constants.CONN_STR,
            container_name=constants.BLOB_NAME
        )  
        gmail_reader.list_labels()
        gmail_reader.select_inbox()
        gmail_reader.fetch_emails()
        return HttpResponse("Successfully fetched and stored emails.", status_code=200)
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return HttpResponse(f"An error occurred: {e}", status_code=500)


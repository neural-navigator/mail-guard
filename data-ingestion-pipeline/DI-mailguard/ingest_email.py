import imaplib
import email
import json
import logging
from azure.storage.blob import BlobServiceClient
from datetime import datetime


class GmailReader:
    def __init__(self, email_user, email_pass, azure_conn_str, container_name):
        logging.basicConfig(level=logging.INFO)
        try:
            self.mail = imaplib.IMAP4_SSL("imap.gmail.com")
            self.mail.login(email_user, email_pass)
            self.email_user = email_user
            self.email_pass = email_pass
            self.blob_service_client = BlobServiceClient.from_connection_string(azure_conn_str)
            self.container_name = container_name
            logging.info("Successfully connected to Gmail.")
        except Exception as e:
            logging.error(f"Failed to connect to Gmail: {e}")
            raise

    def list_labels(self):
        """List all labels in the Gmail mailbox."""
        labels = []
        try:
            status, label_list = self.mail.list()
            if status == 'OK':
                logging.info("Successfully fetched mailbox labels.")
                print("Mailbox labels:")
                for label in label_list:
                    labels.append(label.decode('utf-8'))
            else:
                logging.warning("Failed to list mailbox labels.")
        except Exception as e:
            logging.error(f"An error occurred while listing labels: {e}")
        return labels

    def select_inbox(self):
        """Select the inbox for further email operations."""
        try:
            status, _ = self.mail.select("INBOX")
            if status == 'OK':
                logging.info("Successfully selected the inbox.")
            else:
                logging.warning("Failed to select the inbox.")
            return status
        except Exception as e:
            logging.error(f"An error occurred while selecting the inbox: {e}")
            return None

    def fetch_emails(self):
        """Fetch and save emails from all labels."""
        try:
            labels = self.list_labels()
            for label_name in labels:
                label_name = label_name.split(' "/" ')[-1].replace('"', '')

                # Skip labels that are not standard folders
                if "\\" in label_name:
                    continue

                status, _ = self.mail.select(f'"{label_name}"')
                if status != 'OK':
                    logging.warning(f"Failed to select {label_name}.")
                    continue

                status, messages = self.mail.search(None, "ALL")
                if status != 'OK':
                    logging.warning("Failed to search emails.")
                    continue

                email_ids = messages[0].split()
                for e_id in email_ids:  # Loop through all email IDs
                    status, msg_data = self.mail.fetch(e_id, '(RFC822)')
                    raw_email = msg_data[0][1]
                    email_dict = self._parse_email(raw_email)

                    # Add 'label' key to the dictionary
                    if email_dict:
                        email_dict['label'] = label_name

                    self._save_to_json(email_dict, e_id.decode('utf-8'))
            return {'status': 'successfully fetch_emails executed!'}
        except Exception as e:
            logging.error(f"An error occurred while fetching emails: {e}")
            return {'status': 'failed fetch_emails'}
        

    def _parse_email(self, raw_email):
        """Parse raw email and return a dictionary of its components."""
        try:
            email_dict = {"label": ""}
            msg = email.message_from_bytes(raw_email)
            email_dict['Headers'] = {k: v for k, v in msg.items()}
            email_dict['Body'] = []

            if msg.is_multipart():
                for part in msg.walk():
                    part_dict = {}
                    content_type = part.get_content_type()
                    part_dict['Content_Type'] = content_type
                    try:
                        body = part.get_payload(decode=True).decode()
                        part_dict['Body'] = body
                    except:
                        part_dict['Body'] = None
                    email_dict['Body'].append(part_dict)
            else:
                try:
                    email_dict['Body'] = msg.get_payload(decode=True).decode()
                except:
                    email_dict['Body'] = None

            return email_dict
        except Exception as e:
            logging.error(f"An error occurred while parsing an email: {e}")
            return None

    def _save_to_json(self, email_dict, e_id):
        try:
            email_json = json.dumps(email_dict, indent=4)
            self._upload_to_azure(email_json, e_id)
        except Exception as e:
            logging.error(f"An error occurred while saving to JSON: {e}")

    def _upload_to_azure(self, email_json, e_id):
        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            blob_name = f"{datetime.now().strftime('%Y-%m-%d')}/email_{e_id}.json"
            blob_client = container_client.get_blob_client(blob_name)
            blob_client.upload_blob(email_json, overwrite=True)
            logging.info(f"Successfully uploaded email_{e_id}.json to Azure Blob.")
            return {'status': 'successfully uploaded to azure!'}
        except Exception as e:
            logging.error(f"An error occurred while uploading to Azure Blob: {e}")
            return {'status': 'failed in _upload_to_azure'}
        

    def run(self):
        self.list_labels()
        self.select_inbox()
        self.fetch_emails()


import imaplib
import email
import json
import logging


class GmailReader:
    """Class for reading and saving emails from Gmail."""
    def __init__(self, email_user, email_pass):
        """Initialize with Gmail username and password."""
        logging.basicConfig(level=logging.INFO)
        try:
            self.mail = imaplib.IMAP4_SSL("imap.gmail.com")
            self.mail.login(email_user, email_pass)
            self.email_user = email_user
            self.email_pass = email_pass
            logging.info("Successfully connected to Gmail.")
        except Exception as e:
            logging.error(f"Failed to connect to Gmail: {e}")
            raise

    def list_labels(self):
        """List all labels in the Gmail mailbox."""
        try:
            status, label_list = self.mail.list()
            if status == 'OK':
                logging.info("Successfully fetched mailbox labels.")
                print("Mailbox labels:")
                for label in label_list:
                    print(label.decode('utf-8'))
            else:
                logging.warning("Failed to list mailbox labels.")
        except Exception as e:
            logging.error(f"An error occurred while listing labels: {e}")

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

    def fetch_emails(self, num_emails=10):
        """Fetch and save up to num_emails emails from the inbox."""
        try:
            status, messages = self.mail.search(None, "ALL")
            if status != 'OK':
                logging.warning("Failed to search emails.")
                return

            email_ids = messages[0].split()
            c = 0
            for e_id in email_ids:
                status, msg_data = self.mail.fetch(e_id, '(RFC822)')
                raw_email = msg_data[0][1]
                email_dict = self._parse_email(raw_email)
                self._save_to_json(email_dict, e_id.decode('utf-8'))

                c += 1
                if c >= num_emails:
                    logging.info(f"{num_emails} emails stored.")
                    break
        except Exception as e:
            logging.error(f"An error occurred while fetching emails: {e}")

    def _parse_email(self, raw_email):
        """Parse raw email and return a dictionary of its components."""
        try:
            email_dict = {}
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
        """Save email data to a JSON file."""
        try:
            email_json = json.dumps(email_dict, indent=4)
            with open(f"email_{e_id}.json", "w") as f:
                f.write(email_json)
        except Exception as e:
            logging.error(f"An error occurred while saving to JSON: {e}")

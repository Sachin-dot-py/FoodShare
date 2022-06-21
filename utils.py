import os
import hashlib
import requests
from secret_config import MAILGUN_API_KEY, MAILGUN_DOMAIN_NAME


def hash_password(password: str, salt: bytes = None) -> tuple[bytes, bytes]:
    """ Takes in a password as a string and returns a randomly generated salt and the hash """
    if not salt:  # If salt is not specified
        salt = os.urandom(64)

    if len(salt) != 64:  # Validates function argument
        raise ValueError("Salt must be a string of 64 characters")

    hashed = hashlib.pbkdf2_hmac('sha256', password.encode("utf-8"), salt, 100000)
    return hashed, salt


def send_email(subject: str, content: str, sender: str, receivers: list[str]) -> requests.Response:
    """ Sends an email using the MailGun API """
    return requests.post(
        f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN_NAME}/messages",
        auth=("api", MAILGUN_API_KEY),
        data={"from": sender,
              "to": receivers,
              "subject": subject,
              "html": content}
    )

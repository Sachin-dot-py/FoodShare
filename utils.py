# System imports:
import os
import hashlib
import smtplib
import ssl
from functools import wraps
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Third-party imports:
import requests

# Local imports:
from secret_config import ORS_API_KEY, EMAIL_ADDRESS, EMAIL_PASSWORD


def cache_data(func):
    cached = {}

    @wraps(func)
    def decorator(*args):
        # args[1:] is being used to exclude the first argument, 'self, which stores the object instance.
        if args[1:] not in cached:
            cached[args[1:]] = func(*args)
            if len(cached) >= 256:  # If the cache is full, delete the oldest item to prevent memory overflow
                cached.pop(next(iter(cached)))
        return cached[args[1:]]

    return decorator


def hash_password(password: str, salt: bytes = None) -> tuple[bytes, bytes]:
    """ Takes in a password as a string and returns a randomly generated salt and the hash """
    if not salt:  # If salt is not specified
        salt = os.urandom(64)

    if len(salt) != 64:  # Validates function argument
        raise ValueError("Salt must be 64 characters")

    hashed = hashlib.pbkdf2_hmac('sha256', password.encode("utf-8"), salt, 100000)
    return hashed, salt


def send_email(subject: str, content: str, sender: str, receivers: list[str]) -> None:
    """ Sends an email from the FoodShare email account """
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = ",".join(receivers)
    message.attach(MIMEText(content, "html"))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(sender, ",".join(receivers), message.as_string())


class ORS:
    """ Used for accessing the Open Route Service API's methods """

    def __init__(self):
        self.key = ORS_API_KEY
        self.base_link = "https://api.openrouteservice.org"

    def _perform_get_request(self, endpoint: str, params: dict):
        """ Internal function to perform a get request to the ORS API given the endpoint and parameters """
        return requests.get(
            self.base_link + endpoint,
            params={"api_key": self.key, **params}
        ).json()

    def _perform_post_request(self, endpoint: str, data: dict):
        """ Internal function to perform a post request to the ORS API given the endpoint and parameters """
        return requests.post(
            self.base_link + endpoint,
            headers={"Authorization": self.key},
            json=data
        ).json()

    def autocomplete_coordinates(self, address: str) -> dict[str, list[float, float]]:
        """ Returns a dictionary mapping name to coordinates of location results for a given address """
        result = self._perform_get_request(
            "/geocode/autocomplete",
            params={
                'text': address,
                'size': 5  # How many results we want
            }
        )

        locations = {}
        for feature in result['features']:
            coordinates = feature['geometry']['coordinates']  # Coordinates of the found location
            name = feature['properties']['label']  # Name of the found location
            locations[name] = coordinates
        return locations

    def get_coordinates(self, address: str) -> list[float, float]:
        """ Returns coordinates (longitude and latitude) for a given address"""
        result = self._perform_get_request(
            "/geocode/search",
            params={
                'text': address,
                'size': 1  # Only first result is required
            }
        )

        # Returns only the coordinates
        return result['features'][0]['geometry']['coordinates']

    @cache_data
    def distance_between(self, coord1: tuple[float, float], coord2: tuple[float, float]) -> float:
        """ Get the distance between two coordinates in metres as an integer"""
        result = self._perform_post_request(
            "/v2/matrix/foot-walking",
            data={
                'locations': [coord1, coord2],
                'metrics': ["distance"],
                'units': "m"
            }
        )
        distance = result['distances'][0][1] or result['distances'][1][0]
        
        return int(distance)

# System imports:
import os
import hashlib

# Third-party imports:
import requests

# Local imports:
from secret_config import MAILGUN_API_KEY, MAILGUN_DOMAIN_NAME, ORS_API_KEY


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

    def autocomplete_coordinates(self, address: str) -> dict[str, list[int, int]]:
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

    def get_coordinates(self, address: str) -> list[int, int]:
        """ Returns coordinates (latitude and longitude) for a given address"""
        result = self._perform_get_request(
            "/geocode/search",
            params={
                'text': address,
                'size': 1  # Only first result is required
            }
        )

        # Returns only the coordinates
        return result['features'][0]['geometry']['coordinates']

    def distance_between(self, coord1: list[int, int], coord2: list[int, int]) -> int:
        """ Get the distance between two coordinates in metres as an integer"""
        result = self._perform_post_request(
            "/v2/matrix/foot-walking",
            data={
                'locations': [coord1, coord2],
                'metrics': ["distance"]
            }
        )

        distance = result['distances'][0][0] or result['distances'][0][1]
        
        return distance

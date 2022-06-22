import pymongo
import random
import time
from utils import hash_password
from secret_config import DB_ACCESS_LINK


class UserDB:
    def __init__(self):
        self.client = pymongo.MongoClient(DB_ACCESS_LINK, server_api=pymongo.server_api.ServerApi('1'))
        self.db = self.client.FoodShare
        self.col = self.db.users

    def add_user(self, fname: str, lname: str, email: str, address: dict, unhashed_password: str) -> None:
        """
        Address is of the form {'name': 'Full Address', 'coordinates' : [longitude, latitude]}
        """
        hashed_password, salt = hash_password(unhashed_password)
        user = {'fname': fname, 'lname': lname, 'email': email.lower(), 'address': address,
                'hashed_password': hashed_password, 'salt': salt}
        self.col.insert_one(user)

    def edit_user(self, email: str, **kwargs) -> None:
        """
        Edit a user's details given their email
        Kwargs can contain: fname, lname, addressed, unhashed_password, salt
        """
        if kwargs.get("unhashed_password", None):
            user = self.get_user(email)
            hashed_password, salt = hash_password(kwargs.pop('unhashed_password'), user['salt'])
            kwargs['hashed_password'] = hashed_password
        self.col.update_one({"email": email.lower()}, {"$set": kwargs})

    def get_user(self, email: str) -> dict:
        user = self.col.find_one({'email': email.lower()}, {"_id": 0})
        return user if user else None  # Return the user if found else None

    def check_credentials(self, email: str, check_password: str) -> bool:
        user = self.get_user(email)
        if not user:  # Account does not exist
            return False
        hashed_password, salt = hash_password(check_password, user['salt'])
        return user['hashed_password'] == hashed_password  # If password is correct

    def delete_user(self, email: str) -> None:
        self.col.delete_one({'email': email.lower()})

    def is_admin(self, email: str) -> bool:
        user = self.get_user(email)
        if user.get("admin", None):  # Returns "True" for admins, "None" for others as the property is not set.
            return True
        return False

    def generate_reset_id(self, email: str) -> int:
        """
        Returns a randomly generated unique id associated with a user
        to reset the user's password given their email address
        """
        reset_id = random.randint(10000000000000, 99999999999999)
        while self.lookup_reset_id(reset_id):  # Keep generating IDs until a unique one is found
            reset_id = random.randint(10000000000000, 99999999999999)
        reset_expiry = int(time.time() + 60*10)  # Reset ID expires 10 minutes from now
        # Update in database so we can reverse lookup the user from the id when the reset link is clicked
        self.col.update_one({"email": email.lower()}, {"$set": {'reset_id': reset_id, 'reset_expiry': reset_expiry}})
        return reset_id

    def lookup_reset_id(self, reset_id: int) -> dict:
        """ Looks up a reset id in the database and returns the user associated with it """
        return self.col.find_one({'reset_id': reset_id}, {'_id': 0})

    def delete_reset_id(self, reset_id: int) -> None:
        """ Removes a reset id from the database once it has been used/has expired """
        self.col.update_one({'reset_id': reset_id}, {"$unset": {"reset_id": "", "reset_expiry": ""}})

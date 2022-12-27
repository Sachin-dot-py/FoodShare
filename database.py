# System imports:
import os
import random
import time
from typing import Union

# Third-party imports:
import pymongo
from bson import ObjectId

# Local imports:
from utils import hash_password
from secret_config import DB_ACCESS_LINK
from config import UPLOADS_FOLDER


class UserDB:
    """ Used to perform actions related to users in the MongoDB Database """
    def __init__(self):
        self.client = pymongo.MongoClient(DB_ACCESS_LINK, server_api=pymongo.server_api.ServerApi('1'))
        self.db = self.client.FoodShare
        self.col = self.db.users

    def add_user(self, fname: str, lname: str, email: str, address: dict, unhashed_password: str) -> bool:
        """ Adds a user to the database.

        Args:
            fname: The first name of the user.
            lname: The last name of the user.
            email: The email address of the user. (must be unique)
            address: Address in the form {'name': 'Full Address', 'coordinates' : [longitude, latitude]}.
            unhashed_password: The password inputted by the user.

        Returns:
            True if successful, False if a user already exists with the given email address.
        """
        if self.get_user(email):
            return False

        hashed_password, salt = hash_password(unhashed_password)
        user = {'fname': fname, 'lname': lname, 'email': email.lower(), 'address': address,
                'hashed_password': hashed_password, 'salt': salt}
        self.col.insert_one(user)
        return True

    def edit_user(self, email: str, **kwargs) -> None:
        """ Edit a user's details given their email address.

        Args:
            email: The email address of the user.
            **kwargs: Arbitrary keyword arguments of details to change.
        """
        if kwargs.get("unhashed_password", None):
            user = self.get_user(email)
            hashed_password, salt = hash_password(kwargs.pop('unhashed_password'), user['salt'])
            kwargs['hashed_password'] = hashed_password
        self.col.update_one({"email": email.lower()}, {"$set": kwargs})

    def get_user(self, email: str) -> dict:
        """ Fetch a user from the database given their email address.

        Args:
            email: The email address of the user.

        Returns:
            A dict consisting of the user details if found, else None.
        """
        user = self.col.find_one({'email': email.lower()}, {"_id": 0})
        return user if user else None  # Return the user if found else None

    def get_all_users(self) -> list[dict]:
        """ Fetch all the users from the database.

        Returns:
            A list containing multiple dicts, each representing one user.
        """
        users = list(self.col.find({}, {"_id": 0}))
        return users

    def check_credentials(self, email: str, check_password: str) -> bool:
        """ Verifies a password against their hashed password in the database.

        Args:
            email: The email address of the user.
            check_password: The password to verify (unhashed).

        Returns:
            True if the password is correct, False otherwise.

        Raises:
            ValueError: If the account does not exist.
        """
        user = self.get_user(email)
        if not user:
            raise ValueError("The user does not exist.")
        hashed_password, salt = hash_password(check_password, user['salt'])
        return user['hashed_password'] == hashed_password  # If password is correct

    def delete_user(self, email: str) -> None:
        """ Deletes a user from the database.

        Args:
            email: The email address of the user.
        """
        self.col.delete_one({'email': email.lower()})

    def is_admin(self, email: str) -> bool:
        """ Checks if a user is an admin in the database.

        Args:
            email: The email address of the user.

        Returns:
            True if the user is an admin, False otherwise.

        Raises:
            ValueError: If the account does not exist.
        """
        user = self.get_user(email)
        if not user:
            raise ValueError("The user does not exist.")

        return user.get("admin", False)

    def generate_reset_id(self, email: str) -> int:
        """ Returns an id associated with a user to reset their password given their email address.

        Args:
            email: The email address of the user.

        Returns:
            A unique reset id.
        """
        reset_id = random.randint(10000000000000, 99999999999999)
        while self.lookup_reset_id(reset_id):  # Keep generating IDs until a unique one is found
            reset_id = random.randint(10000000000000, 99999999999999)
        reset_expiry = int(time.time() + 60*10)  # Reset ID expires 10 minutes from now
        # Update in database so we can reverse lookup the user from the id when the reset link is clicked
        self.col.update_one({"email": email.lower()}, {"$set": {'reset_id': reset_id, 'reset_expiry': reset_expiry}})
        return reset_id

    def lookup_reset_id(self, reset_id: int) -> dict:
        """ Looks up a reset id in the database and returns the user associated with it.

        Args:
            reset_id: The reset id to look up.

        Returns:
            The user associated with the reset id.
        """
        return self.col.find_one({'reset_id': reset_id}, {'_id': 0})

    def delete_reset_id(self, reset_id: int) -> None:
        """ Removes a reset id from the database once it has been used/has expired

        Args:
            reset_id: The reset id to delete.
        """
        self.col.update_one({'reset_id': reset_id}, {"$unset": {"reset_id": "", "reset_expiry": ""}})


class RestaurantsDB:
    """ Used to perform actions related to restaurants in the MongoDB Database """
    def __init__(self):
        self.client = pymongo.MongoClient(DB_ACCESS_LINK, server_api=pymongo.server_api.ServerApi('1'))
        self.db = self.client.FoodShare
        self.col = self.db.restaurants

    def add_restaurant(self, email: str, name: str, address: dict, coverpic: str) -> bool:
        """ Adds a restaurant to the database.

        Args:
            email: The email address of the user who owns the restaurant.
            name: The name of the restaurant.
            address: Address in the form {'name': 'Full Address', 'coordinates' : [longitude, latitude]}.
            coverpic: Filename of the restaurant cover picture

        Returns:
            True if successful, False if a restaurant already exists with the given name.

        Raises:
            ValueError: If restaurant already exists with the given email address.
        """
        if self.get_restaurant(name=name):
            return False
        if self.get_restaurant(email=email):
            raise ValueError("A restaurant already exists with the given name/email address.")

        restaurant = {'email': email.lower(), 'name': name, 'address': address, 'coverpic': coverpic}
        self.col.insert_one(restaurant)
        return True

    def edit_restaurant(self, email: str, **kwargs) -> None:
        """ Edit a restaurant's details given the email address of its owner.

        Args:
            email: The email address of the user who owns the restaurant.
            **kwargs: Arbitrary keyword arguments of details to change.
        """

        self.col.update_one({"email": email.lower()}, {"$set": kwargs})

    def get_restaurant(self, name: str = None, restid: str = None, email: str = None) -> dict:
        """ Fetches a restaurant from the database given name, email or its unique id.

        Args:
            name: The name of the restaurant.
            restid: The unique ID of the restaurant.
            email: The email address of the user who owns the restaurant.

        Returns:
            A dict consisting of the restaurant details if found, else None.

        Raises:
            ValueError: If name, restaurant id, and email all are not provided.
        """
        if name:
            restaurant = self.col.find_one({'name': name})
        elif restid:
            restaurant = self.col.find_one({'_id': ObjectId(restid)})
        elif email:
            restaurant = self.col.find_one({'email': email.lower()})
        else:
            raise ValueError("Either name, restaurant id, or email must be specified as arguments.")

        return restaurant if restaurant else None

    def view_restaurant(self, name: str = None, restid: str = None, email: str = None) -> dict:
        """ Fetches a restaurant from the database along with its menu items given name or email.

        Args:
            name: The name of the restaurant.
            restid: The unique ID of the restaurant.
            email: The email address of the user who owns the restaurant.

        Returns:
            A dict consisting of the restaurant details if found, else None.

        Raises:
            ValueError: If name, restaurant id, and email all are not provided.
        """
        if name:
            match = {'name': name}
        elif restid:
            match = {'_id': ObjectId(restid)}
        elif email:
            match = {'email': email.lower()}
        else:
            raise ValueError("Either name, restaurant id, or email must be specified as arguments.")

        restaurant = self.col.aggregate([
            {
                "$match": match
            },
            {
                "$lookup": {
                    "from": "fooditems",
                    "localField": "menu",
                    "foreignField": "_id",
                    "as": "menu"
                }
            }]
        )
        return list(restaurant)[0] if restaurant else None

    def get_all_restaurants(self) -> list[dict]:
        """ Fetches all restaurants from the database .

        Returns:
            A list of dicts consisting of the restaurant details.
        """
        return list(self.col.find())


class FoodItemsDB:
    """ Used to perform actions related to food items in the MongoDB Database """
    def __init__(self):
        self.client = pymongo.MongoClient(DB_ACCESS_LINK, server_api=pymongo.server_api.ServerApi('1'))
        self.db = self.client.FoodShare
        self.col = self.db.fooditems

    def add_item(self, restid: Union[str, ObjectId], name: str, description: str, price: float,
                 restrictions: dict, picture: str = None) -> ObjectId:
        """ Adds a restaurant to the database.

        Args:
            restid: Id of the restaurant whom the food item is being added for.
            name: The name of the food item.
            description: Description of the food item.
            price: Price of the food item, in dollars.
            restrictions: Dietary restrictions, as a dictionary.
            picture: Filename of the food item in the uploads folder (optional).

            Restrictions is of the form:
            {
                "vegetarian": True,
                "vegan": False,
                "allergens": "Contains peanut."
            }

        Returns:
            The _id of the inserted food item

        Raises:
            FileNotFoundError: If the picture (if passed to the function) does not exist.
            ValueError: If the price is a negative number.
        """

        if not isinstance(restid, ObjectId):
            restid = ObjectId(restid)

        if picture:
            path = os.path.join(os.getcwd(), UPLOADS_FOLDER, picture)
            if not os.path.isfile(path):
                raise FileNotFoundError(f"File {picture} does not exist in the uploads folder.")

        if price < 0:
            raise ValueError("Price cannot be negative.")

        price = round(price, 2)  # Round to 2 decimal places
        item = {'restid': ObjectId(restid), 'name': name, 'description': description, 'price': price,
                'restrictions': restrictions, 'picture': picture}
        result = self.col.insert_one(item)
        return result.inserted_id

    def edit_item(self, itemid: Union[str, ObjectId], **kwargs) -> None:
        """ Edit a restaurant's details given the email address of its owner.

        Args:
            itemid: The unique ID of the food item.
            **kwargs: Arbitrary keyword arguments of details to change.
        """

        if not isinstance(itemid, ObjectId):
            itemid = ObjectId(itemid)

        self.col.update_one({"_id": itemid}, {"$set": kwargs})

    def get_item(self, itemid: Union[str, ObjectId]) -> dict:
        """ Fetches a food item from the database given its id.

        Args:
            itemid: The unique ID of the food item.

        Returns:
            A dict consisting of the food item details if found, else None.
        """
        if not isinstance(itemid, ObjectId):
            itemid = ObjectId(itemid)
        item = self.col.find_one({'_id': itemid})

        return item or None

    def get_items(self, restid: str) -> list[dict]:
        """ Fetches all food items added by a restaurant from the database.

        Args:
            restid: The unique ID of the restaurant being queried.

        Returns:
            A list of dicts consisting of each food item.
        """
        return list(self.col.find({"restid": restid}))

    def get_menu(self, menu: dict) -> list[dict]:
        """ Fetches the details of the food items in the menu of the restaurant from the database.

        Args:
            menu: The menu containing a list of Object Id's

        Returns:
            A list of dicts consisting of each food item.
        """
        return list(self.col.find({"_id": {"$in": menu}}))

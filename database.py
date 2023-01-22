# System imports:
import json
import os
import random
import time
from typing import Union

# Third-party imports:
import mysql.connector

# Local imports:
from utils import hash_password
from secret_config import MYSQL_DB_USERNAME, MYSQL_DB_PASSWORD
from config import UPLOADS_FOLDER


class MySQL:
    """ Superclass used to provide an interface with the MySQL Database through Inheritance """
    def __init__(self):
        self.db = mysql.connector.connect(
            host="localhost",
            user=MYSQL_DB_USERNAME,
            password=MYSQL_DB_PASSWORD
        )
        self.cur = self.db.cursor(dictionary=True)
        with open("setup_db.sql", "r") as f:
            self.cur.execute(f.read(), multi=True)  # Create database and tables during first run
        self.cur.execute("USE foodshare")

    def _insert(self, table_name: str, data: dict[str, Union[str, int, float, bool]]) -> int:
        """ Inserts a record into the specified table with the specified details

        Args:
            table_name: The name of the table to insert to.
            data: The fields and values that are being inserted as a dictionary.

        Returns:
            The ID of the inserted record.
        """
        fields = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        # Values are passed separately below to prevent SQL injection as they are user inputs.
        self.cur.execute(f"INSERT INTO {table_name} ({fields}) VALUES ({placeholders})", list(data.values()))
        self.db.commit()
        return self.cur.lastrowid

    def _select(self, table_name: str, fields: list[str], where: dict[str, Union[str, int, float, bool]] = None , select_one=False) -> Union[list[dict], dict]:
        """ Selects a record from the specified table with the specified details

        Args:
            table_name: The name of the table to select from.
            columns: The fields to select from the table.
            where: The fields and their corresponding values as a dictionary.
            select_one: Whether to select one record or all records.

        Returns:
            The selected record(s).

        Note:
            Pass fields=["*"] to select all fields.
        """
        fields_query = ", ".join(fields)
        if where:
            where_query = " AND ".join([f"{key} = %s" for key in where.keys()])
            # Values are passed separately below to prevent SQL injection as they are user inputs.
            self.cur.execute(f"SELECT {fields_query} FROM {table_name} WHERE {where_query}", list(where.values()))
        else:
            self.cur.execute(f"SELECT {fields_query} FROM {table_name}")
        if select_one:
            return self.cur.fetchone()
        else:
            return self.cur.fetchall()

    def _update(self, table_name: str, data: dict[str, Union[str, int, float, bool]], where: dict[str, Union[str, int, float, bool]]):
        """ Updates a record from the specified table with the specified details

        Args:
            table_name: The name of the table to update.
            data: The fields and new values to be updated as a dictionary.
            where: The fields and values that are being selected as a dictionary.
        """
        data_query = ", ".join([f"{key} = %s" for key in data.keys()])
        where_query = " AND ".join([f"{key} = %s" for key in where.keys()])
        # Values are passed separately below to prevent SQL injection as they are user inputs.
        self.cur.execute(f"UPDATE {table_name} SET {data_query} WHERE {where_query}", list(data.values()) + list(where.values()))
        self.db.commit()

    def _delete(self, table_name: str, where: dict[str, Union[str, int, float, bool]]):
        """ Deletes a record from the specified table with the specified details

        Args:
            table_name: The name of the table to delete from.
            where: The fields and values that are being selected as a dictionary.
        """
        where_query = " AND ".join([f"{key} = %s" for key in where.keys()])
        # Values are passed separately below to prevent SQL injection as they are user inputs.
        self.cur.execute(f"DELETE FROM {table_name} WHERE {where_query}", list(where.values()))
        self.db.commit()


class UserDB(MySQL):
    """ Used to perform actions related to users in the SQL Database """
    def __init__(self):
        super().__init__()  # Initialize database

    def add_user(self, fname: str, lname: str, email: str, address: str, longitude: float, latitude: float, unhashed_password: str) -> Union[bool, int]:
        """ Adds a user to the database.

        Args:
            fname: The first name of the user.
            lname: The last name of the user.
            email: The email address of the user. (must be unique)
            address: Full Address of the user
            longitude: Longitude of the user's address
            latitude: Latitude of the user's address
            unhashed_password: The password inputted by the user.

        Returns:
            userid if successful, False if a user already exists with the given email address.
        """
        if self.get_user(email):
            return False

        hashed_password, salt = hash_password(unhashed_password)
        user = {'fname': fname, 'lname': lname, 'email': email.lower(), 'address': address, 'longitude': round(longitude, 6),
                'latitude': round(latitude, 6), 'hashed_password': hashed_password, 'salt': salt}
        userid = self._insert("users", user)
        return userid

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
        self._update("users", kwargs, {"email": email.lower()})

    def get_user(self, email: str = None, userid: int = None) -> Union[dict, None]:
        """ Fetch a user from the database given their email address.

        Args: (only one of the below)
            email: The email address of the user.
            userid: The ID of the user.

        Returns:
            A dict consisting of the user details if found, else None.

        Raises:
            ValueError: If both email and userid are not provided.
        """
        if email:
            user = self._select("users", ["*"], {"email": email.lower()}, select_one=True)
        elif userid:
            user = self._select("users", ["*"], {"userid": userid}, select_one=True)
        else:
            raise ValueError("Must provide either email or userid")

        if user:
            user['hashed_password'] = bytes(user['hashed_password'])
            user['salt'] = bytes(user['salt'])
            user['longitude'] = float(user['longitude'])
            user['latitude'] = float(user['latitude'])
            return user
        else:
            return None

    def get_all_users(self) -> list[dict]:
        """ Fetch all the users from the database.

        Returns:
            A list containing multiple dicts, each representing one user.
        """
        users = self._select("users", ["*"])
        return users

    def check_credentials(self, email: str, check_password: str) -> Union[bool, dict]:
        """ Verifies a password against their hashed password in the database.

        Args:
            email: The email address of the user.
            check_password: The password to verify (unhashed).

        Returns:
            True if the password is correct, False otherwise or if the account doesn't exist.
        """
        user = self.get_user(email)
        if not user:
            return False
        hashed_password, salt = hash_password(check_password, user['salt'])
        if user['hashed_password'] == hashed_password:  # If password is correct
            return user

    def delete_user(self, email: str) -> None:
        """ Deletes a user from the database.

        Args:
            email: The email address of the user.
        """
        self._delete("users", {"email": email.lower()})

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
        reset_expiry = int(time.time() + 60*10)  # Reset ID expires 10 minutes from now (unix timestamp)
        # Update in database so we can reverse lookup the user from the id when the reset link is clicked
        self._update("users", {"reset_id": reset_id, "reset_expiry": reset_expiry}, {"email": email.lower()})
        return reset_id

    def lookup_reset_id(self, reset_id: int) -> dict:
        """ Looks up a reset id in the database and returns the user associated with it.

        Args:
            reset_id: The reset id to look up.

        Returns:
            The user associated with the reset id.
        """
        user = self._select("users", ["*"], {"reset_id": reset_id}, select_one=True)
        return user if user else None  # Return the user if found else None

    def delete_reset_id(self, reset_id: int) -> None:
        """ Removes a reset id from the database once it has been used/has expired

        Args:
            reset_id: The reset id to delete.
        """
        self._update("users", {"reset_id": None, "reset_expiry": None}, {"reset_id": reset_id})


class RestaurantsDB(MySQL):
    """ Used to perform actions related to restaurants in the SQL Database """
    def __init__(self):
        super().__init__()  # Initialize database

    def add_restaurant(self, userid: int, name: str, address: str, longitude: float, latitude: float, coverpic: str) -> Union[int, bool]:
        """ Adds a restaurant to the database.

        Args:
            userid: The id of the user who owns the restaurant.
            name: The name of the restaurant.
            address: Full Address of the restaurant.
            longitude: Longitude of the restaurant's address.
            latitude: Latitude of the restaurant's address.
            coverpic: Filename of the restaurant cover picture.

        Returns:
            Restaurant ID if successful, False if a restaurant already exists with the given name.

        Raises:
            ValueError: If restaurant already exists with the given userid.
        """
        if self.get_restaurant(name=name):
            return False
        if self.get_restaurant(userid=userid):
            raise ValueError("A restaurant already exists with the given email address.")

        restaurant = {'userid': userid, 'name': name, 'address': address, 'longitude': longitude,
                      'latitude': latitude, 'coverpic': coverpic}
        restid = self._insert("restaurants", restaurant)
        return restid

    def edit_restaurant(self, userid: int, **kwargs) -> None:
        """ Edit a restaurant's details given the userid of its owner.

        Args:
            email: The userid of the user who owns the restaurant.
            **kwargs: Arbitrary keyword arguments of details to change.
        """

        self._update("restaurants", kwargs, {"userid": userid})

    def get_restaurant(self, name: str = None, restid: int = None, userid: int = None) -> dict:
        """ Fetches a restaurant from the database given name, email or its unique id.

        Args:
            name: The name of the restaurant.
            restid: The unique ID of the restaurant.
            userid: The userid of the user who owns the restaurant.

        Returns:
            A dict consisting of the restaurant details if found, else None.

        Raises:
            ValueError: If name, restaurant id, and userid all are not provided.
        """
        if name:
            restaurant = self._select("restaurants", ["*"], {"name": name}, select_one=True)
        elif restid:
            restaurant = self._select("restaurants", ["*"], {"restid": restid}, select_one=True)
        elif userid:
            restaurant = self._select("restaurants", ["*"], {"userid": userid}, select_one=True)
        else:
            raise ValueError("Either name, restaurant id, or userid must be specified as arguments.")

        if restaurant:
            restaurant['longitude'] = float(restaurant['longitude'])
            restaurant['latitude'] = float(restaurant['latitude'])
            if restaurant['avgreview']: restaurant['avgreview'] = float(restaurant['avgreview'])

        return restaurant if restaurant else None

    def view_restaurant(self, name: str = None, restid: int = None, userid: int = None) -> dict:
        """ Fetches a restaurant from the database along with its menu items given name or restid or userid.

        Args:
            name: The name of the restaurant.
            restid: The unique ID of the restaurant.
            userid: The userid of the user who owns the restaurant.

        Returns:
            A dict consisting of the restaurant details if found, else None.

        Raises:
            ValueError: If name, restid, and userid all are not provided.
        """
        restaurant = self.get_restaurant(name=name, restid=restid, userid=userid)
        if restaurant:
            restaurant['menu'] = FoodItemsDB().fetch_menu(restaurant['restid'])
            if restaurant['avgreview']: restaurant['avgreview'] = float(restaurant['avgreview'])
        return restaurant

    def get_all_restaurants(self) -> list[dict]:
        """ Fetches all restaurants from the database .

        Returns:
            A list of dicts consisting of the restaurant details.
        """
        restaurants = self._select("restaurants", ["*"])
        for restaurant in restaurants:
            restaurant['longitude'] = float(restaurant['longitude'])
            restaurant['latitude'] = float(restaurant['latitude'])
            if restaurant['avgreview']: restaurant['avgreview'] = float(restaurant['avgreview'])
        return restaurants


class FoodItemsDB(MySQL):
    """ Used to perform actions related to food items in the SQL Database """
    def __init__(self):
        super().__init__()  # Initialize database

    def add_item(self, restid: int, name: str, description: str, price: float,
                 restrictions: dict, picture: str = None) -> int:
        """ Adds a restaurant to the database.

        Args:
            restid: Id of the restaurant whom the food item is being added for.
            name: The name of the food item.
            description: Description of the food item.
            price: Price of the food item, in dollars.
            restrictions: Dietary restrictions, as a list.
            picture: Filename of the food item in the uploads folder (optional).

        Returns:
            The itemid of the inserted food item

        Raises:
            FileNotFoundError: If the picture (if passed to the function) does not exist.
            ValueError: If the price is a negative number.
        """

        if picture:
            path = os.path.join(os.getcwd(), UPLOADS_FOLDER, picture)
            if not os.path.isfile(path):
                raise FileNotFoundError(f"File {picture} does not exist in the uploads folder.")

        if price < 0:
            raise ValueError("Price cannot be negative.")

        price = round(price, 2)  # Round to 2 decimal places
        item = {'restid': restid, 'name': name, 'description': description, 'price': price,
                'restrictions': ", ".join(restrictions), 'picture': picture}
        itemid = self._insert("fooditems", item)
        return itemid

    def edit_item(self, itemid: int, **kwargs) -> None:
        """ Edit a restaurant's details given the email address of its owner.

        Args:
            itemid: The unique ID of the food item.
            **kwargs: Arbitrary keyword arguments of details to change.
        """
        if 'restrictions' in kwargs.keys():
            kwargs['restrictions'] = ", ".join(kwargs['restrictions'])
        self._update("fooditems", kwargs, {"itemid": itemid})

    def remove_item(self, itemid: int):
        """ Removes a food item from the database.

        Args:
            itemid: The unique ID of the food item.
        """
        self._delete("fooditems", {"itemid": itemid})

    def get_item(self, itemid: int) -> dict:
        """ Fetches a food item from the database given its id.

        Args:
            itemid: The unique ID of the food item.

        Returns:
            A dict consisting of the food item details if found, else None.
        """
        item = self._select("fooditems", ["*"], {"itemid": itemid}, select_one=True)
        if item:
            item['price'] = float(item['price'])
            item['restrictions'] = item['restrictions'].split(", ")
        return item if item else None

    def fetch_items(self, restid: int) -> list[dict]:
        """ Fetches all food items added by a restaurant from the database.

        Args:
            restid: The unique ID of the restaurant being queried.

        Returns:
            A list of dicts consisting of each food item.
        """
        items = self._select("fooditems", ["*"], {"restid": restid})
        for item in items:
            item['price'] = float(item['price'])
            item['restrictions'] = item['restrictions'].split(", ")
        return items

    def fetch_menu(self, restid: int) -> list[dict]:
        """ Fetches all food items added by a restaurant and in the menu from the database.

        Args:
            restid: The unique ID of the restaurant being queried.

        Returns:
            A list of dicts consisting of each food item.
        """
        menu = self._select("fooditems", ["*"], {"restid": restid, "inmenu": True})
        for item in menu:
            item['price'] = float(item['price'])
            item['restrictions'] = item['restrictions'].split(", ")
        return menu


class CartDB(MySQL):
    """ Used to perform actions related to users' carts in the SQL Database """
    def __init__(self):
        super().__init__()  # Initialize database

    def increment_item(self, userid: int, itemid: int):
        """ Adds/increments an item to the cart of the user.

        Args:
            userid: Id of the user whom the item is being added to.
            itemid: Id of the item being added.

        Returns:
            True if the item was added to the cart, False if the item mismatches with the preexisting restaurant.

        Raises:
            ValueError: If items from multiple restaurants are being added to cart.
        """
        cart = self.fetch_cart(userid)
        if cart:
            if cart[0]['restid'] != FoodItemsDB().get_item(itemid)['restid']:
                raise ValueError("Cannot add items from multiple restaurants to the cart.")

        cart = {item['itemid']: item['quantity'] for item in cart}

        if itemid in cart.keys():  # If item is already in cart
            self._update("cart", {"quantity": cart[itemid] + 1}, {"userid": userid, "itemid": itemid})
        else:
            self._insert("cart", {"userid": userid, "itemid": itemid, "quantity": 1, "restid": FoodItemsDB().get_item(itemid)['restid']})

    def decrement_item(self, userid: int, itemid: int) -> None:
        """ Removes/decrements an item from the cart of the user.

        Args:
            userid: Id of the user whom the item is being removed from.
            itemid: Id of the item being removed.

        Raises:
            ValueError: If the item is not in the cart.
        """
        cart = self.fetch_cart(userid)
        cart = {item['itemid']: item['quantity'] for item in cart}

        if itemid in cart.keys():
            if cart[itemid] == 1:  # Decrement to zero = Delete
                self._delete("cart", {"userid": userid, "itemid": itemid})
            else:
                self._update("cart", {"quantity": cart[itemid] - 1}, {"userid": userid, "itemid": itemid})
        else:
            raise ValueError("Item not in cart.")

    def fetch_cart(self, userid: int) -> list[dict]:
        """ Fetches all cart items added by a user from the database.

        Args:
            userid: The unique ID of the user being queried.

        Returns:
            A list of dicts consisting of each cart item.
        """
        items = self._select("cart", ["restid", "itemid", "quantity"], {"userid": userid})
        return items

    def clear_cart(self, userid: int):
        """ Clears the cart of the user.

        Args:
            userid: The unique ID of the user being queried.
        """
        self._delete("cart", {"userid": userid})


class OrdersDB(MySQL):
    """ Used to perform actions related to orders in the SQL Database """
    def __init__(self):
        super().__init__()  # Initialize database

    def create_order(self, userid: int, restid: int, items: list[dict], amount: float) -> int:
        """ Adds an order to the database.

        Args:
            userid: The unique ID of the user placing the order.
            restid: The unique ID of the restaurant the order is being placed at.
            items: A list of dicts containing the itemid, name, quantity, and price of each item in the order.
            amount: The total price of the order.

        Returns:
            The unique ID of the order.
        """
        order = {'userid': userid, 'restid': restid, 'items': json.dumps(items), 'amount': amount, 'ordertime': time.time()}
        orderid = self._insert("orders", order)
        return orderid

    def mark_ready(self, orderid: int):
        """ Marks an order as ready.

        Args:
            orderid: The unique ID of the order.
        """
        self._update("orders", {"orderstatus": "Ready"}, {"orderid": orderid})

    def mark_collected(self, orderid: int):
        """ Marks an order as collected.

        Args:
            orderid: The unique ID of the order.
        """
        self._update("orders", {"orderstatus": "Collected"}, {"orderid": orderid})

    def cancel_order(self, orderid: int):
        """ Cancels an order.

        Args:
            orderid: The unique ID of the order being cancelled.
        """
        self._delete("orders", {"orderid": orderid})

    def fetch_user_orders(self, userid: int) -> list[dict]:
        """ Fetches all orders placed by a user from the database.

        Args:
            userid: The unique ID of the user being queried.

        Returns:
            A list of dicts consisting of each order.
        """
        orders = self._select("orders", ["*"], {"userid": userid})
        for order in orders:
            order['items'] = json.loads(order['items'])
        return orders

    def fetch_rest_orders(self, restid: int) -> list[dict]:
        """ Fetches all orders placed at a restaurant from the database.

        Args:
            restid: The unique ID of the restaurant being queried.

        Returns:
            A list of dicts consisting of each order.
        """
        orders = self._select("orders", ["*"], {"restid": restid})
        for order in orders:
            order['items'] = json.loads(order['items'])
        return orders

    def fetch_order(self, orderid: int) -> dict:
        """ Fetches an order from the database given its id.

        Args:
            orderid: The unique ID of the order.

        Returns:
            A dict consisting of the order details
        """
        order = self._select("orders", ["*"], {"orderid": orderid}, select_one=True)
        order['items'] = json.loads(order['items'])
        return order


class ContactFormResponsesDB(MySQL):
    """ Used to store contact form responses in the SQL Database """
    def __init__(self):
        super().__init__()  # Initialize database

    def add_response(self, response) -> None:
        """ Adds a response to the database.

        Args:
            response: A dict containing the following response details:
                fname: The first name of the person who submitted the form.
                lname: The last name of the person who submitted the form.
                email: The email of the person who submitted the form.
                message: The message of the person who submitted the form.
                nature: The nature of the message.
                submittedat: The time the form was submitted.
                message: The message.
        """
        self._insert("contactformresponses", response)

    def fetch_responses(self) -> list[dict]:
        """ Fetches all responses from the database.

        Returns:
            A list of dicts consisting of each response.
        """
        responses = self._select("contactformresponses", ["*"])
        return responses


class ReviewsDB(MySQL):
    """ Used to store reviews in the SQL Database """
    def __init__(self):
        super().__init__()  # Initialize database

    def add_review(self, orderid: int, stars: int, title: str, description: str) -> int:
        """ Adds a review to the database and updates the restaurants table with the new rating.

        Args:
            orderid: The unique ID of the order the review is for.
            stars: The number of stars given in the review.
            title: The title of the review.
            description: The description of the review.

        Returns:
            The unique ID of the review.
        """
        # Insert into reviews table
        order = OrdersDB().fetch_order(orderid)
        review = {'orderid': orderid, 'stars': stars, 'title': title, 'description': description, 'submittedat': time.time(),
                  'userid': order['userid'], 'restid': order['restid']}
        reviewid = self._insert("reviews", review)

        # Update restaurant's overall rating
        rdb = RestaurantsDB()
        restaurant = rdb.get_restaurant(restid=order['restid'])
        if restaurant['numreviews'] > 0:
            newrating = (restaurant['avgreview'] * restaurant['numreviews'] + stars) / (restaurant['numreviews'] + 1)
        else:
            newrating = stars
        rdb.edit_restaurant(restaurant['userid'], **{'avgreview': round(newrating, 2), 'numreviews': restaurant['numreviews'] + 1})

        return reviewid

    def fetch_rest_reviews(self, restid: int) -> list[dict]:
        """ Fetches all reviews for a restaurant from the database.

        Args:
            restid: The unique ID of the restaurant being queried.

        Returns:
            A list of dicts consisting of each review.
        """
        reviews = self._select("reviews", ["*"], {"restid": restid})
        return reviews

    def fetch_user_reviews(self, userid: int) -> list[dict]:
        """ Fetches all reviews by a user from the database.

        Args:
            userid: The unique ID of the user being queried.

        Returns:
            A list of dicts consisting of each review.
        """
        reviews = self._select("reviews", ["*"], {"userid": userid})
        return reviews

    def fetch_review(self, reviewid: int) -> dict:
        """ Fetches a review from the database given its id.

        Args:
            reviewid: The unique ID of the review.

        Returns:
            A dict consisting of the review details
        """
        review = self._select("reviews", ["*"], {"reviewid": reviewid}, select_one=True)
        return review

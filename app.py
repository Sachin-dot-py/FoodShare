# System imports:
import os
import re
import time
import logging
from functools import wraps
from datetime import datetime

# Third-party imports:
from flask import Flask, request, render_template, session, redirect, url_for, abort, jsonify, send_from_directory
from werkzeug.utils import secure_filename

# Local imports:
from database import UserDB, RestaurantsDB, FoodItemsDB, CartDB, OrdersDB, ContactFormResponsesDB, ReviewsDB
from utils import send_email, ORS
from config import *
from secret_config import FLASK_SECRET_KEY, GOOGLE_API_KEY

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = 8 * 1000 * 1000  # Limiting uploads to 8 megabytes

logging.basicConfig(filename='FoodShare.log', level=logging.INFO, format='%(asctime)s %(levelname)s : %(message)s')


@app.template_filter()
def format_date(epoch_time: int) -> str:
    """ Converts epoch time to a readable date format for use in the html templates """
    return datetime.fromtimestamp(epoch_time).strftime('%d %b %Y')


@app.template_filter()
def format_datetime(epoch_time: int) -> str:
    """ Converts epoch time to a readable date and time format for use in the html templates """
    return datetime.fromtimestamp(epoch_time).strftime('%d %b %Y, %I:%M %p')


@app.template_filter()
def fetch_user(userid: int):
    """ Returns the user with the given userid for use in the html templates """
    return UserDB().get_user(userid=userid)


# Decorator function for pages requiring a login
def login_required(func):
    @wraps(func)
    def decorator(*args, **kwargs):
        if not session.get('email', None):
            return redirect(url_for('login_page', next=request.url, alert='Please login to continue'))
        return func(*args, **kwargs)

    return decorator


# Decorator function to render error pages given name & description
def error_page(func):
    @wraps(func)
    def decorator(*args, **kwargs):
        params = func(*args, **kwargs)
        return render_template('error.html', **params), params['error']

    return decorator


@app.route("/", methods=["GET"])
def home_page():
    logged_in = bool(session.get("email", None))
    if logged_in:
        return redirect(url_for("buyer_dashboard"))
    else:
        return render_template("home.html", alert=request.args.get("alert"))


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    error = None
    if request.method == 'POST':  # Login form has been submitted
        db = UserDB()
        if user := db.check_credentials(request.form['email'], request.form['password']):
            session['email'] = request.form['email']
            session['userid'] = user['userid']
            if request.form['keep_me_logged_in']:
                session.permanent = True
            if request.form['next']:  # If user was initially redirected to the login page
                return redirect(request.form['next'])
            else:
                return redirect(url_for("buyer_dashboard", alert="Welcome back!"))
        else:
            error = 'The credentials you have entered are incorrect. Please try again.'

    if session.get('email', None):  # If user is already logged in
        return redirect(url_for("buyer_dashboard"))

    return render_template('login.html', error=error, alert=request.args.get('alert', None),
                           next=request.form.get('next', ''))


@app.route('/sign_up', methods=["GET", "POST"])
def sign_up_page():
    error = None
    if request.method == "POST":
        db = UserDB()
        if db.get_user(request.form['email']):  # Check if the user already has an account.
            error = "An account with the given email address already exists. " \
                    "Please use a different email address or login to your existing account."
        else:  # Sign the user up
            # Although we have client-side validation of user-provided details, we still
            # validate the most important details on server-side for certainty.
            valid = True
            if request.form['fname'] == "": valid = False
            if request.form['lname'] == "": valid = False
            if request.form['email'] == "": valid = False
            if not re.search(EMAIL_REGEX, request.form['email']): valid = False  # Is provided email valid?
            if request.form['address'] == "": valid = False
            if request.form['password'] == "": valid = False
            if request.form['password'] != request.form['repassword']: valid = False

            if valid:
                api = ORS()
                coordinates = api.get_coordinates(request.form['address'])
                userid = db.add_user(request.form['fname'], request.form['lname'], request.form['email'],
                                     request.form['address'],
                                     coordinates[0], coordinates[1], request.form['password'])
                message = WELCOME_TEMPLATE.format(fname=request.form['fname'])
                send_email("Welcome to FoodShare", message, COMMS_EMAIL, [request.form['email']])
                # Sign the user in and redirect to the dashboard
                session['email'] = request.form['email']
                session['userid'] = userid
                return redirect(url_for("buyer_dashboard"))
            else:
                error = "Please fill in all the fields correctly according to the provided instructions."

    #  Sign up page is opened (GET request) or signup form submitted with existing account
    return render_template("sign_up.html", error=error)


@app.route('/reset_password', methods=["GET", "POST"])
def reset_password_page():
    if request.method == "GET":  # User opening the webpage
        return render_template("change_reset_password.html", stage=1)  # Render form with email address
    else:  # Submitting the form with the email address
        db = UserDB()
        user = db.get_user(request.form['email'])
        if not user:  # Invalid email address
            error = "The email address provided does not match any existing accounts." \
                    "Please create a new account or try another email address."
            return render_template("change_reset_password.html", stage=1, error=error)
        reset_id = db.generate_reset_id(request.form['email'])
        link = f"{WEBSITE_BASE_URL}/reset_password/{reset_id}"
        content = RESET_PASSWORD_TEMPLATE.format(fname=user['fname'], link=link, SUPPORT_EMAIL=SUPPORT_EMAIL)
        send_email("Reset your password", content, COMMS_EMAIL, [request.form['email']])
        return render_template("change_reset_password.html", stage=2)  # Message informing user to check their email


@app.route('/reset_password/<int:reset_id>', methods=["GET", "POST"])
def reset_password(reset_id: int):
    if request.method == "GET":  # User opening the webpage from the email link
        db = UserDB()
        user = db.lookup_reset_id(reset_id)
        if not user:  # Invalid URL or already used reset ID
            error = "We're sorry, but your reset link is invalid. Please generate a new one below to continue."
            return render_template("change_reset_password.html", stage=1, error=error)  # Redirect back to first stage
        if user['reset_expiry'] < time.time():  # Reset ID has expired
            db.delete_reset_id(reset_id)
            error = "We're sorry, but your reset link has expired. Please generate a new one below to continue."
            return render_template("change_reset_password.html", stage=1, error=error)  # Redirect back to first stage
        return render_template("change_reset_password.html", stage=3, reset_id=reset_id,
                               fname=user['fname'])  # Render form with email address
    else:  # Submitting the form with the email address
        db = UserDB()
        user = db.lookup_reset_id(reset_id)
        db.edit_user(user['email'], unhashed_password=request.form['password'])  # Change the password
        db.delete_reset_id(reset_id)
        message = RESET_PASSWORD_NOTIFICATION.format(fname=user['fname'], SUPPORT_EMAIL=SUPPORT_EMAIL)
        send_email("Your password has been reset", message, COMMS_EMAIL, [user['email']])  # Notify the user by email
        session['email'] = user['email']  # Sign the user in
        session['userid'] = user['userid']
        return redirect(url_for("buyer_dashboard", alert="Your password has been successfully changed."))


@app.route("/profile/edit", methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == "GET":  # User opening the webpage
        return render_template("change_reset_password.html", alert=request.args.get("alert"), change_password=True)
    else:  # Form submitted
        db = UserDB()
        user = db.get_user(session['email'])
        db.edit_user(user['email'], unhashed_password=request.form['password'])
        message = CHANGE_PASS_NOTIF.format(fname=user['fname'], SUPPORT_EMAIL=SUPPORT_EMAIL)
        send_email("Your password has been changed", message, COMMS_EMAIL, [user['email']])  # Notify the user by email
        return redirect(url_for("change_password", alert="Your password has been changed."), code=303)


@app.route('/logout', methods=['GET'])
def logout_page():
    session.pop('email', None)
    session.pop('userid', None)
    return redirect(url_for('home_page', alert="You have been logged out."))


@app.route('/contact_us', methods=["GET", "POST"])
def contact_us():
    if request.method == "GET":
        return render_template("contact_us.html", signed_in=bool(session.get('email')))
    else:
        ContactFormResponsesDB().add_response(dict(request.form) | {'submittedat': time.time()})
        message = CONTACT_US_RESPONSE.format(fname=request.form['fname'], lname=request.form['lname'],
                                             email=request.form['email'], message=request.form['message'],
                                             nature=request.form['nature'])
        send_email(f"New {request.form['nature'].lower()} from FoodShare", message, COMMS_EMAIL, [SUPPORT_EMAIL])

        return render_template("contact_us.html", signed_in=bool(session.get('email')),
                               alert="Your message has been sent. We will get back to you shortly.")


@app.route('/autocomplete/address', methods=['GET'])
def address_autocomplete():
    # Provides autocomplete details to the frontend
    if address := request.args.get("address", None):  # Check if the request is valid
        api = ORS()
        return jsonify(api.autocomplete_coordinates(address))
    else:
        abort(400)


@app.route("/restaurants", methods=['GET'])
@login_required
def buyer_dashboard():
    udb = UserDB()
    user = udb.get_user(session['email'])
    rdb = RestaurantsDB()
    restaurants = rdb.get_all_restaurants()
    api = ORS()
    user_coords = (user['longitude'], user['latitude'])
    for restaurant in restaurants:
        #  Calculate distance between user and restaurant
        restaurant_coords = (restaurant['longitude'], restaurant['latitude'])
        distance = api.distance_between(user_coords, restaurant_coords)
        restaurant['distance'] = distance
    restaurants = sorted(restaurants, key=lambda restaurant: restaurant['distance'])  # Sort restaurants by distance
    return render_template("buyer_dashboard.html", restaurants=restaurants, alert=request.args.get('alert', None))


@app.route("/restaurants/<int:restid>", methods=['GET'])
@login_required
def view_restaurant(restid: int):
    rdb = RestaurantsDB()
    restaurant = rdb.view_restaurant(restid=restid)
    udb = UserDB()
    user = udb.get_user(session['email'])
    api = ORS()
    restaurant_coords = (restaurant['longitude'], restaurant['latitude'])
    user_coords = (user['longitude'], user['latitude'])
    restaurant['distance'] = api.distance_between(user_coords, restaurant_coords)
    restaurant['menu'] = [restaurant['menu'][x:x + 4] for x in
                          range(0, len(restaurant['menu']), 4)]  # Split into groups of 4
    cart = CartDB().fetch_cart(session['userid'])
    cart = {item['itemid']: item['quantity'] for item in cart}
    return render_template("restaurant.html", restaurant=restaurant, cart=cart, GOOGLE_API_KEY=GOOGLE_API_KEY)


@app.route("/cart/update", methods=['POST'])
@login_required
def update_cart():
    cdb = CartDB()
    try:
        if request.form['action'] == 'increment':  # User clicked the "+" button
            cdb.increment_item(session['userid'], int(request.form['itemid']))
        elif request.form['action'] == 'decrement':  # User clicked the "-" button
            cdb.decrement_item(session['userid'], int(request.form['itemid']))
    except ValueError:
        abort(400)  # Signal to frontend that the request was invalid.

    return 'Successful', 200


@app.route("/cart/view", methods=['GET'])
@login_required
def view_cart():
    rdb = RestaurantsDB()
    cdb = CartDB()
    cart = cdb.fetch_cart(session['userid'])
    if cart:
        restaurant = rdb.view_restaurant(restid=cart[0]['restid'])
        fdb = FoodItemsDB()
        items = []
        for item in cart:
            details = fdb.get_item(item['itemid'])
            details['quantity'] = item['quantity']
            details['total'] = round(details['quantity'] * details['price'], 2)
            items.append(details)
        total = sum(item['total'] for item in items)
        return render_template("cart.html", cart=items, total=total, restaurant=restaurant,
                               alert=request.args.get('alert'))
    else:
        return render_template("cart.html", cart=[])


@app.route("/cart/submit", methods=['POST'])
@login_required
def submit_cart():
    if request.form['action'] == 'checkout':  # User clicked the "Checkout" button
        cdb = CartDB()
        cart = cdb.fetch_cart(session['userid'])
        rdb = RestaurantsDB()
        restaurant = rdb.view_restaurant(restid=cart[0]['restid'])

        if not restaurant['open']:  # If the restaurant is not accepting new orders
            return redirect(url_for('view_cart',
                                    alert="Your order was not sent, as the restaurant is currently not accepting new orders. Please try again later."))

        fdb = FoodItemsDB()
        items = []
        for item in cart:
            details = fdb.get_item(item['itemid'])
            details['quantity'] = item['quantity']
            details['total'] = round(details['quantity'] * details['price'], 2)
            items.append(details)
        amount = sum(item['total'] for item in items)

        #  Process order:
        odb = OrdersDB()
        orderid = odb.create_order(session['userid'], restaurant['restid'], items, amount)
        cdb.clear_cart(session['userid'])

        #  Send emails to buyer and seller:
        udb = UserDB()
        buyer = udb.get_user(session['email'])
        seller = udb.get_user(userid=restaurant['userid'])

        buyer_message = ORDER_CONFIRM_BUYER.format(orderid=orderid, fname=buyer['fname'],
                                                   link=url_for('buyer_orders', _external=True))
        send_email(f"Order Confirmation #{orderid} at {restaurant['name']}", buyer_message, COMMS_EMAIL, [session['email']])

        seller_message = ORDER_CONFIRM_SELLER.format(orderid=orderid, fname=seller['fname'],
                                                     link=url_for('seller_dashboard', _external=True),
                                                     buyer=buyer['fname'], amount=round(amount, 2))
        send_email(f"New Order #{orderid} by {buyer['fname']} {buyer['lname']}", seller_message, COMMS_EMAIL, [seller['email']])

        return redirect(url_for('buyer_orders', alert=f"Your order at {restaurant['name']} for ${amount} has been placed!"))
    elif request.form['action'] == 'clear':  # User clicked "Clear Cart"
        cdb = CartDB()
        cdb.clear_cart(session['userid'])
        return redirect(url_for('buyer_dashboard', alert="Your cart has been cleared."))


@app.route("/seller/setup", methods=['GET', 'POST'])
@login_required
def setup_restaurant():
    rdb = RestaurantsDB()
    if request.method == "GET":  # Opening the webpage
        if rdb.get_restaurant(userid=session['userid']):  # User has set up their restaurant
            return redirect(url_for("seller_dashboard"))
        else:
            return render_template("setup_restaurant.html", allowed_extensions=", ".join(ALLOWED_FILE_EXTENSIONS))
    else:  # Submitting the form
        file = request.files['coverpic']
        if not file.filename.lower().endswith(ALLOWED_FILE_EXTENSIONS):  # Check if file is of a permitted format
            return render_template("setup_restaurant.html", allowed_extensions=", ".join(ALLOWED_FILE_EXTENSIONS)
                                   , error="Invalid file extension. Please upload only image files.")
        extension = "." + file.filename.split(".")[-1]
        coverpic = secure_filename(request.form['name'] + extension)
        path = os.path.join(os.getcwd(), UPLOADS_FOLDER, coverpic)
        while coverpic == "" or os.path.exists(path):
            coverpic = "1" + coverpic  # Keeps prepending "1" to the filename until it is unique/valid
            path = os.path.join(os.getcwd(), UPLOADS_FOLDER, coverpic)
        file.save(path)

        api = ORS()
        coordinates = api.get_coordinates(request.form['address'])

        rdb.add_restaurant(session['userid'], request.form['name'], request.form['address'], coordinates[0],
                           coordinates[1], coverpic)
        return redirect(url_for("seller_dashboard"))


@app.route("/seller/dashboard", methods=['GET'])
@login_required
def seller_dashboard():
    rdb = RestaurantsDB()
    if restaurant := rdb.get_restaurant(userid=session['userid']):  # User has set up their restaurant
        odb = OrdersDB()
        orders = odb.fetch_rest_orders(restaurant['restid'])
        udb = UserDB()
        for order in orders:
            order['restaurant'] = restaurant
            order['date'] = datetime.fromtimestamp(order['ordertime']).strftime("%d %b %Y")
            order['time'] = datetime.fromtimestamp(order['ordertime']).strftime("%I:%M %p")
            order['buyer'] = udb.get_user(userid=order['userid'])
        return render_template("seller_dashboard.html", orders=orders, restaurant=restaurant)
    else:
        return redirect(url_for("setup_restaurant"))


@app.route("/orders/toggle", methods=['POST'])
@login_required
def toggle_orders():
    rdb = RestaurantsDB()
    rdb.edit_restaurant(session['userid'], **{"open": request.form['toggle'] == 'true'})  # Toggle "Accept Orders" status
    return 'Successful', 200


@app.route("/orders/markready", methods=['POST'])
@login_required
def mark_order_ready():
    orderid = int(request.form['orderid'])
    rdb = RestaurantsDB()
    restaurant = rdb.get_restaurant(userid=session['userid'])
    odb = OrdersDB()
    order = odb.fetch_order(orderid)
    udb = UserDB()
    buyer = udb.get_user(userid=order['userid'])
    if order['restid'] == restaurant['restid']:
        odb.mark_ready(orderid)  # Marks the order as ready in the database
        send_email(f"Order #{orderid} is ready for pickup",
                   ORDER_READY_FOR_COLLECTION.format(orderid=orderid, fname=buyer['fname'],
                                                     restaurant=restaurant['name'], address=restaurant['address']),
                   COMMS_EMAIL, [buyer['email']])  # Inform user that order is ready for pickup
        return 'Successful', 200
    else:
        return 'Unauthorized', 401


@app.route("/orders/markcollected", methods=['POST'])
@login_required
def mark_order_collected():
    orderid = int(request.form['orderid'])
    rdb = RestaurantsDB()
    restaurant = rdb.get_restaurant(userid=session['userid'])
    odb = OrdersDB()
    order = odb.fetch_order(orderid)
    if order['restid'] == restaurant['restid']:
        odb.mark_collected(orderid)  # Mark the order as collected in the database
        return 'Successful', 200
    else:
        return 'Unauthorized', 401


@app.route("/orders/cancel", methods=['POST'])
@login_required
def cancel_order():
    odb = OrdersDB()
    order = odb.fetch_order(orderid=int(request.form['orderid']))
    rdb = RestaurantsDB()
    restaurant = rdb.get_restaurant(restid=order['restid'])
    udb = UserDB()

    if order['userid'] == session['userid']:  # Order is being cancelled by the buyer
        buyer = udb.get_user(email=session['email'])
        odb.cancel_order(orderid=int(request.form['orderid']))
        send_email(f"Order #{request.form['orderid']} Cancelled",
                   ORDER_CANCELLED_BY_BUYER.format(orderid=request.form['orderid'],
                                                   buyer=buyer['fname'] + " " + buyer['lname']),
                   COMMS_EMAIL, [session['email']])
        return "Successful", 200
    elif session['userid'] == restaurant['userid']:  # Order is being cancelled by the seller
        buyer = udb.get_user(userid=order['userid'])
        odb.cancel_order(orderid=int(request.form['orderid']))
        send_email(f"Order #{request.form['orderid']} Cancelled",
                   ORDER_CANCELLED_BY_SELLER.format(orderid=request.form['orderid'], restaurant=restaurant['name']),
                   COMMS_EMAIL, [buyer['email']])
        return "Successful", 200
    else:
        return "Unauthorized", 401


@app.route("/orders/invoice/<int:orderid>", methods=['GET'])
@login_required
def generate_invoice(orderid: int):
    odb = OrdersDB()
    order = odb.fetch_order(orderid=orderid)
    rdb = RestaurantsDB()
    restaurant = rdb.get_restaurant(restid=order['restid'])
    udb = UserDB()
    user = udb.get_user(userid=order['userid'])
    # Check if the user logged-in is either the buyer or seller
    if restaurant['userid'] == session['userid'] or user['userid'] == session['userid']:
        order['date'] = datetime.fromtimestamp(order['ordertime']).strftime("%d %b %Y")
        order['time'] = datetime.fromtimestamp(order['ordertime']).strftime("%I:%M %p")
        return render_template("invoice.html", order=order, restaurant=restaurant, buyer=user)
    else:
        return "Unauthorized", 401


@app.route("/buyer/orders", methods=['GET'])
@login_required
def buyer_orders():
    odb = OrdersDB()
    orders = odb.fetch_user_orders(session['userid'])
    reviewdb = ReviewsDB()
    reviews = reviewdb.fetch_user_reviews(session['userid'])
    reviews = {review['orderid']: review['stars'] for review in reviews}
    rdb = RestaurantsDB()
    for order in orders:
        order['restaurant'] = rdb.get_restaurant(restid=order['restid'])
        order['date'] = datetime.fromtimestamp(order['ordertime']).strftime("%d %b %Y")
        order['time'] = datetime.fromtimestamp(order['ordertime']).strftime("%I:%M %p")
        order['review'] = reviews.get(order['orderid'], None)  # "None" if the user has not reviewed the order yet.
    return render_template("buyer_orders.html", orders=orders)


@app.route("/reviews/add", methods=['POST'])
@login_required
def add_review():
    orderid = int(request.form['orderid'])
    stars = int(request.form['stars'])
    title = request.form['title']
    description = request.form['description']
    order = OrdersDB().fetch_order(orderid)
    if order['userid'] == session['userid']:
        reviewdb = ReviewsDB()
        reviewdb.add_review(orderid, stars, title, description)
        return 'Successful', 200
    else:
        return 'Unauthorized', 401


@app.route("/reviews/view/<int:restid>", methods=['GET'])
@login_required
def view_reviews(restid: int):
    reviewdb = ReviewsDB()
    reviews = reviewdb.fetch_rest_reviews(restid)
    rdb = RestaurantsDB()
    restaurant = rdb.get_restaurant(restid=restid)
    if restaurant['userid'] == session['userid']:  # If the user is the owner of the restaurant
        return render_template("reviews.html", reviews=reviews, restaurant=restaurant, is_owner=True)
    else:
        return render_template("reviews.html", reviews=reviews, restaurant=restaurant, is_owner=False)


@app.route("/restaurant/edit", methods=['GET', 'POST'])
@login_required
def edit_restaurant():
    if request.method == 'GET':  # User is opening the webpage
        rdb = RestaurantsDB()
        if restaurant := rdb.get_restaurant(userid=session['userid']):  # User has set up their restaurant
            fooditems = FoodItemsDB().fetch_items(restaurant['restid'])
            return render_template("edit_restaurant.html", restaurant=restaurant, fooditems=fooditems,
                                   alert=request.args.get('alert'))
        else:
            return redirect(url_for("setup_restaurant"))
    else:  # User has submitted the form
        api = ORS()
        coordinates = api.get_coordinates(request.form['address'])
        restaurant = {'name': request.form['name'], 'address': request.form['address'], 'longitude': coordinates[0],
                      'latitude': coordinates[1]}

        file = request.files.get('coverpic')
        if file:
            if not file.filename.lower().endswith(ALLOWED_FILE_EXTENSIONS):
                return render_template("setup_restaurant.html", allowed_extensions=", ".join(ALLOWED_FILE_EXTENSIONS)
                                       , error="Invalid file extension. Please upload only image files.")
            extension = "." + file.filename.split(".")[-1]
            coverpic = secure_filename(request.form['name'] + extension)
            path = os.path.join(os.getcwd(), UPLOADS_FOLDER, coverpic)
            while coverpic == "" or os.path.exists(path):
                coverpic = "1" + coverpic  # Keeps prepending "1" to the filename until it is unique/valid
                path = os.path.join(os.getcwd(), UPLOADS_FOLDER, coverpic)
            file.save(path)
            restaurant['coverpic'] = coverpic

        rdb = RestaurantsDB()
        rdb.edit_restaurant(session['userid'], **restaurant)
        return redirect(url_for("edit_restaurant", alert="Restaurant details updated successfully"))


@app.route("/menu/update", methods=['POST'])
@login_required
def update_menu():
    rdb = RestaurantsDB()
    restaurant = rdb.get_restaurant(userid=session['userid'])
    fdb = FoodItemsDB()
    item = fdb.get_item(int(request.form['itemid']))
    if item['restid'] == restaurant['restid']:  # Validate that item is actually owned by this user.
        fdb.edit_item(int(request.form['itemid']), **{'inmenu': True if request.form.get('menu') == "on" else False})
    return redirect(url_for("edit_restaurant", alert=f"Successfully toggled {item['name']} in the menu"),
                    code=303)  # 303 forces the POST into a GET request


@app.route("/fooditem/add", methods=['POST'])
@login_required
def add_food_item():
    rdb = RestaurantsDB()
    restaurant = rdb.get_restaurant(userid=session['userid'])
    fdb = FoodItemsDB()
    restrictions = request.form.getlist('dietary')
    file = request.files['itemimg']
    if file.filename.lower().endswith(ALLOWED_FILE_EXTENSIONS):
        extension = "." + file.filename.split(".")[-1]
        coverpic = secure_filename(request.form['name'] + extension)
        path = os.path.join(os.getcwd(), UPLOADS_FOLDER, coverpic)
        while coverpic == "" or os.path.exists(path):
            coverpic = "1" + coverpic  # Keeps prepending "1" to the filename until it is unique/valid
            path = os.path.join(os.getcwd(), UPLOADS_FOLDER, coverpic)
        file.save(path)
    else:
        coverpic = "defaultitem.png"
    fdb.add_item(restaurant['restid'], request.form['name'].strip("'"), request.form['description'].strip("'"),
                 float(request.form['price']), restrictions, coverpic)
    return redirect(url_for("edit_restaurant", alert=f"Successfully added {request.form['name']} to your food list"),
                    code=303)  # 303 forces the POST into a GET request


@app.route("/fooditem/edit", methods=['POST'])
@login_required
def edit_food_item():
    rdb = RestaurantsDB()
    restaurant = rdb.get_restaurant(userid=session['userid'])
    fdb = FoodItemsDB()
    restrictions = request.form.getlist('dietary')
    item = {'name': request.form['name'].strip("'"), 'description': request.form['description'].strip("'"),
            'price': float(request.form['price']), 'restrictions': restrictions}
    if request.files.get("itemimg", None):
        file = request.files['itemimg']
        if file.filename.lower().endswith(ALLOWED_FILE_EXTENSIONS):
            extension = "." + file.filename.split(".")[-1]
            coverpic = secure_filename(request.form['name'] + extension)
            path = os.path.join(os.getcwd(), UPLOADS_FOLDER, coverpic)
            while coverpic == "" or os.path.exists(path):
                coverpic = "1" + coverpic  # Keeps prepending "1" to the filename until it is unique/valid
                path = os.path.join(os.getcwd(), UPLOADS_FOLDER, coverpic)
            file.save(path)
        else:
            coverpic = "defaultitem.png"
        item['picture'] = coverpic
    if fdb.get_item(int(request.form['itemid']))['restid'] == restaurant['restid']:  # Validate that item is actually owned by this user.
        fdb.edit_item(int(request.form['itemid']), **item)
    return redirect(url_for("edit_restaurant", alert=f"Successfully edited {request.form['name']} on your food list"),
                    code=303)  # 303 forces the POST into a GET request


@app.route("/fooditem/delete", methods=['POST'])
@login_required
def delete_food_item():
    rdb = RestaurantsDB()
    restaurant = rdb.get_restaurant(userid=session['userid'])
    fdb = FoodItemsDB()
    if fdb.get_item(int(request.form['itemid']))['restid'] == restaurant['restid']:  # Validate that item is actually owned by this user.
        fdb.remove_item(int(request.form['itemid']))
    return redirect(
        url_for("edit_restaurant", alert=f"Successfully deleted {request.form['name']} from your food list"),
        code=303)  # 303 forces the POST into a GET request


# Allows users to view the image files uploaded here
@app.route('/uploads/<string:name>')
def view_upload(name: str):
    return send_from_directory(UPLOADS_FOLDER, name)


# Error Handlers:

@app.errorhandler(400)
@error_page
def bad_request(error):
    return {'error': 400, 'name': 'Bad Request',
            'description': 'Your request could not be processed. Please try again.'}


@app.errorhandler(403)
@error_page
def forbidden(error):
    return {'error': 403, 'name': 'Forbidden',
            'description': 'Access to the page you requested to access is restricted.'}


@app.errorhandler(404)
@error_page
def page_not_found(error):
    return {'error': 404, 'name': 'Page not Found', 'description': 'The page you requested could not be found.'}


@app.errorhandler(500)
@error_page
def internal_server_error(error):
    return {'error': 500, 'name': 'Internal Server Error', 'description': 'Oops! Something went wrong.'}


@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon.ico')


if __name__ == '__main__':
    app.run(debug=False)

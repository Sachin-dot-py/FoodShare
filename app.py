# System imports:
import os
import time
from functools import wraps

# Third-party imports:
from flask import Flask, request, render_template, session, redirect, url_for, abort, jsonify, send_from_directory
from werkzeug.utils import secure_filename

# Local imports:
from database import UserDB, RestaurantsDB, FoodItemsDB, CartDB
from utils import send_email, ORS
from config import WEBSITE_BASE_URL, COMMS_EMAIL, SUPPORT_EMAIL, RESET_PASSWORD_TEMPLATE, RESET_PASSWORD_NOTIFICATION, \
    WELCOME_TEMPLATE, CHANGE_PASS_NOTIF, UPLOADS_FOLDER, ALLOWED_FILE_EXTENSIONS
from secret_config import FLASK_SECRET_KEY

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = 8 * 1000 * 1000  # Limiting uploads to 8 megabytes


# Decorator function for pages requiring a login
def login_required(func):
    @wraps(func)
    def decorator(*args, **kwargs):
        if not session.get('email', None):
            return redirect(url_for('loginpage', next=request.url))
        return func(*args, **kwargs)
    return decorator


# Decorator function for admin-only pages
def admin_only(func):
    @wraps(func)
    def decorator(*args, **kwargs):
        userdb = UserDB()
        if not userdb.is_admin(session['email']):
            abort(403)
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
def homepage():
    logged_in = bool(session.get("email", None))
    if logged_in:
        return redirect(url_for("buyerdashboard"))
    else:
        return render_template("home.html")


@app.route('/login', methods=['GET', 'POST'])
def loginpage():
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
                return redirect(url_for("buyerdashboard"))  # TODO decide the landing page
        else:
            error = 'The credentials you have entered are incorrect. Please try again.'

    if session.get('email', None):  # If user is already logged in
        return redirect(url_for("buyerdashboard"))  # TODO decide the landing page

    #  Login page is opened (GET request) or login form submitted with invalid credentials
    return render_template('login.html', error=error, next=request.form.get('next', ""))


@app.route('/sign_up', methods=["GET", "POST"])
def sign_up_page():
    error = None
    if request.method == "POST":
        db = UserDB()
        if db.get_user(request.form['email']):  # Check if the user already has an account.
            error = "An account with the given email address already exists. " \
                    "Please use a different email address or login to your existing account."
            # TODO Server Side Validation
        else:  # Sign the user up
            api = ORS()
            coordinates = api.get_coordinates(request.form['address'])
            userid = db.add_user(request.form['fname'], request.form['lname'], request.form['email'], request.form['address'],
                        coordinates[0], coordinates[1], request.form['password'])
            message = WELCOME_TEMPLATE.format(fname=request.form['fname'])
            send_email("Welcome to FoodShare", message, COMMS_EMAIL, [request.form['email']])
            # Sign the user in and redirect to the dashboard
            session['email'] = request.form['email']
            session['userid'] = userid
            return redirect(url_for("buyerdashboard"))  # TODO decide the landing page

    #  Sign up page is opened (GET request) or signup form submitted with existing account
    return render_template("signup.html", error=error)


@app.route('/reset_password', methods=["GET", "POST"])
def reset_password_page():
    if request.method == "GET":  # User opening the webpage
        return render_template("reset_password.html", stage=1)  # Render form with email address
    else:  # Submitting the form with the email address
        db = UserDB()
        user = db.get_user(request.form['email'])
        if not user:  # Invalid email address
            error = "The email address provided does not match any existing accounts." \
                    "Please create a new account or try another email address."
            return render_template("reset_password.html", stage=1, error=error)
        reset_id = db.generate_reset_id(request.form['email'])
        link = f"{WEBSITE_BASE_URL}/reset_password/{reset_id}"
        content = RESET_PASSWORD_TEMPLATE.format(fname=user['fname'], link=link, SUPPORT_EMAIL=SUPPORT_EMAIL)
        send_email("Reset your password", content, COMMS_EMAIL, [request.form['email']])
        return render_template("reset_password.html", stage=2)  # Message informing user to check their email


@app.route('/reset_password/<int:reset_id>', methods=["GET", "POST"])
def reset_password(reset_id: int):
    if request.method == "GET":  # User opening the webpage from the email link
        db = UserDB()
        user = db.lookup_reset_id(reset_id)
        if not user:  # Invalid URL
            abort(400)
        if user['reset_expiry'] < time.time():  # Reset ID has expired
            db.delete_reset_id(reset_id)
            error = "We're sorry, but your reset link has expired. Please generate a new one below to continue."
            return render_template("reset_password.html", stage=1, error=error)  # Redirect back to first stage
        return render_template("reset_password.html", stage=3, reset_id=reset_id, fname=user['fname'])  # Render form with email address
    else:  # Submitting the form with the email address
        db = UserDB()
        user = db.lookup_reset_id(reset_id)
        db.edit_user(user['email'], unhashed_password=request.form['password'])  # Change the password
        db.delete_reset_id(reset_id)
        message = RESET_PASSWORD_NOTIFICATION.format(fname=user['fname'], SUPPORT_EMAIL=SUPPORT_EMAIL)
        send_email("Your password has been reset", message, COMMS_EMAIL, [user['email']])
        session['email'] = user['email']  # Sign the user in
        # TODO add a flash message saying your password has been changed.
        return redirect(url_for("buyerdashboard"))  # TODO decide the landing page


@app.route("/change_password", methods=['GET', 'POST'])
@login_required
def changepassword():
    if request.method == "GET":  # User opening the webpage
        return render_template("reset_password.html", change_password=True)
    else:  # Form submitted
        db = UserDB()
        user = db.get_user(session['email'])
        db.edit_user(user['email'], unhashed_password=request.form['password'])
        message = CHANGE_PASS_NOTIF.format(fname=user['fname'], SUPPORT_EMAIL=SUPPORT_EMAIL)
        send_email("Your password has been changed", message, COMMS_EMAIL, [user['email']])
        return redirect(url_for("homepage"))  # TODO Change this when the profile/settings page is made


@app.route('/logout', methods=['GET'])
def logoutpage():
    session.pop('email', None)
    session.pop('userid', None)
    return redirect(url_for('homepage'))


@app.route('/autocomplete/address', methods=['GET'])
def address_autocomplete():
    # Check if the request is valid (i.e. the address parameter has been provided
    if address := request.args.get("address", None):
        api = ORS()
        return jsonify(api.autocomplete_coordinates(address))
    else:
        abort(400)


@app.route("/restaurants", methods=['GET'])
@login_required
def buyerdashboard():
    udb = UserDB()
    user = udb.get_user(session['email'])
    rdb = RestaurantsDB()
    restaurants = rdb.get_all_restaurants()
    api = ORS()
    user_coords = (user['longitude'], user['latitude'])
    for restaurant in restaurants:
        restaurant_coords = (restaurant['longitude'], restaurant['latitude'])
        distance = api.distance_between(user_coords, restaurant_coords)
        restaurant['distance'] = distance
    return render_template("buyer_dashboard.html", restaurants=restaurants)


@app.route("/restaurants/<int:restid>", methods=['GET'])
@login_required
def viewrestaurant(restid: int):
    rdb = RestaurantsDB()
    restaurant = rdb.view_restaurant(restid=restid)
    udb = UserDB()
    user = udb.get_user(session['email'])
    api = ORS()
    restaurant_coords = (restaurant['longitude'], restaurant['latitude'])
    user_coords = (user['longitude'], user['latitude'])
    restaurant['distance'] = api.distance_between(restaurant_coords, user_coords)
    restaurant['menu'] = [restaurant['menu'][x:x+4] for x in range(0, len(restaurant['menu']), 4)]  # Split into groups of 4
    cart = CartDB().fetch_cart(session['userid'])
    cart = {item['itemid']: item['quantity'] for item in cart}
    return render_template("restaurant.html", restaurant=restaurant, cart=cart)


@app.route("/cart/update", methods=['POST'])
@login_required
def updatecart():
    cdb = CartDB()
    try:
        if request.form['action'] == 'increment':
            cdb.increment_item(session['userid'], int(request.form['itemid']))
        elif request.form['action'] == 'decrement':
            cdb.decrement_item(session['userid'], int(request.form['itemid']))
    except ValueError:
        abort(400)  # Signal to frontend that the request was invalid.

    return 'Successful', 200

@app.route("/seller/setup", methods=['GET', 'POST'])
@login_required
def setup_restaurant():
    rdb = RestaurantsDB()
    if request.method == "GET":  # Opening the webpage
        if rdb.get_restaurant(userid=session['userid']):  # User has set up their restaurant
            return redirect(url_for("sellerdashboard"))
        else:
            return render_template("setup_restaurant.html", allowed_extensions=", ".join(ALLOWED_FILE_EXTENSIONS))
    else:  # Submitting the form
        file = request.files['coverpic']
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

        api = ORS()
        coordinates = api.get_coordinates(request.form['address'])

        rdb.add_restaurant(session['userid'], request.form['name'], request.form['address'], coordinates[0], coordinates[1], coverpic)
        return redirect(url_for("sellerdashboard"))


@app.route("/seller/dashboard", methods=['GET'])
@login_required
def sellerdashboard():
    rdb = RestaurantsDB()
    if restaurant := rdb.get_restaurant(userid=session['userid']):  # User has set up their restaurant
        raise NotImplementedError()
    else:
        return redirect(url_for("setup_restaurant"))


@app.route("/seller/updatemenu", methods=['GET'])
@login_required
def updatemenu():
    rdb = RestaurantsDB()
    if restaurant := rdb.get_restaurant(userid=session['userid']):  # User has set up their restaurant
        fooditems = FoodItemsDB().fetch_items(restaurant['restid'])
        return render_template("updatemenu.html", restaurant=restaurant, fooditems=fooditems, alert=request.args.get('alert'))
    else:
        return redirect(url_for("setup_restaurant"))

@app.route("/updateinmenu", methods=['POST'])
@login_required
def updateinmenu():
    rdb = RestaurantsDB()
    restaurant = rdb.get_restaurant(userid=session['userid'])
    fdb = FoodItemsDB()
    item = fdb.get_item(int(request.form['itemid']))
    if item['restid'] == restaurant['restid']:  # Validate that item is actually owned by this user.
        fdb.edit_item(int(request.form['itemid']), **{'inmenu': True if request.form.get('menu') == "on" else False})
    return redirect(url_for("updatemenu", alert=f"Successfully toggled {item['name']} in the menu"), code=303)  # 303 forces the POST into a GET request

@app.route("/addfooditem", methods=['POST'])
@login_required
def addfooditem():
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
    fdb.add_item(restaurant['restid'], request.form['name'].strip("'"), request.form['description'].strip("'"), float(request.form['price']), restrictions, coverpic)
    return redirect(url_for("updatemenu", alert=f"Successfully added {request.form['name']} to your food list"), code=303)  # 303 forces the POST into a GET request

@app.route("/editfooditem", methods=['POST'])
@login_required
def editfooditem():
    rdb = RestaurantsDB()
    restaurant = rdb.get_restaurant(userid=session['userid'])
    fdb = FoodItemsDB()
    restrictions = request.form.getlist('dietary')
    item = {'name': request.form['name'].strip("'"), 'description': request.form['description'].strip("'"), 'price': float(request.form['price']), 'restrictions': restrictions}
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
    return redirect(url_for("updatemenu",  alert=f"Successfully edited {request.form['name']} on your food list"), code=303)  # 303 forces the POST into a GET request


@app.route("/deletefooditem", methods=['POST'])
@login_required
def deletefooditem():
    rdb = RestaurantsDB()
    restaurant = rdb.get_restaurant(userid=session['userid'])
    fdb = FoodItemsDB()
    if fdb.get_item(int(request.form['itemid']))['restid'] == restaurant['restid']:  # Validate that item is actually owned by this user.
        fdb.remove_item(int(request.form['itemid']))
    return redirect(url_for("updatemenu",  alert=f"Successfully deleted {request.form['name']} from your food list"), code=303)  # 303 forces the POST into a GET request


@app.route("/admin/dashboard", methods=['GET'])
@login_required
@admin_only
def admindashboard():
    raise NotImplementedError()


# Allows users to view the image files uploaded here
@app.route('/uploads/<string:name>')
def view_upload(name: str):
    return send_from_directory(UPLOADS_FOLDER, name)


# Error Handlers:

@app.errorhandler(400)
@error_page
def bad_request(error):
    return {'error': 400, 'name': 'Bad Request', 'description': 'Your request could not be processed. Please try again.'}


@app.errorhandler(403)
@error_page
def forbidden(error):
    return {'error': 403, 'name': 'Forbidden', 'description': 'Access to the page you requested to access is restricted.'}


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
    app.run(debug=True)

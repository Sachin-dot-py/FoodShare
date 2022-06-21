from flask import Flask, request, render_template, session, redirect, url_for, abort
import time
from functools import wraps
from database import UserDB
from utils import send_email
from config import WEBSITE_BASE_URL, COMMS_EMAIL, SUPPORT_EMAIL, RESET_PASSWORD_TEMPLATE, RESET_PASSWORD_NOTIFICATION, \
    WELCOME_TEMPLATE, CHANGE_PASS_NOTIF
from secret_config import FLASK_SECRET_KEY, DB_ACCESS_LINK

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY


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
        userdb = UserDB(DB_ACCESS_LINK)
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
    return render_template("home.html", logged_in=logged_in)


@app.route('/login', methods=['GET', 'POST'])
def loginpage():
    error = None
    if request.method == 'POST':  # Login form has been submitted
        db = UserDB(DB_ACCESS_LINK)
        if db.check_credentials(request.form['email'], request.form['password']):
            session['email'] = request.form['email']
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
        db = UserDB(DB_ACCESS_LINK)
        if db.get_user(request.form['email']):  # Check if the user already has an account.
            error = "An account with the given email address already exists. " \
                    "Please use a different email address or login to your existing account."
        else:  # Sign the user up
            db.add_user(request.form['fname'], request.form['lname'], request.form['email'], request.form['password'])
            message = WELCOME_TEMPLATE.format(fname=request.form['fname'])
            send_email("Welcome to FoodShare", message, COMMS_EMAIL, [request.form['email']])
            # Sign the user in and redirect to the dashboard
            session['email'] = request.form['email']
            if request.form['keep_me_logged_in']:
                session.permanent = True
            return redirect(url_for("buyerdashboard"))  # TODO decide the landing page

    #  Sign up page is opened (GET request) or signup form submitted with existing account
    return render_template("signup.html", error=error)


@app.route('/reset_password', methods=["GET", "POST"])
def reset_password_page():
    if request.method == "GET":  # User opening the webpage
        return render_template("reset_password.html", stage=1)  # Render form with email address
    else:  # Submitting the form with the email address
        db = UserDB(DB_ACCESS_LINK)
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
        db = UserDB(DB_ACCESS_LINK)
        user = db.lookup_reset_id(reset_id)
        if not user:  # Invalid URL
            abort(400)
        if user['reset_expiry'] < time.time():  # Reset ID has expired
            db.delete_reset_id(reset_id)
            error = "We're sorry, but your reset link has expired. Please generate a new one below to continue."
            return render_template("reset_password.html", stage=1, error=error)  # Redirect back to first stage
        return render_template("reset_password.html", stage=3, reset_id=reset_id, fname=user['fname'])  # Render form with email address
    else:  # Submitting the form with the email address
        db = UserDB(DB_ACCESS_LINK)
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
        db = UserDB(DB_ACCESS_LINK)
        user = db.get_user(session['email'])
        db.edit_user(user['email'], unhashed_password=request.form['password'])
        message = CHANGE_PASS_NOTIF.format(fname=user['fname'], SUPPORT_EMAIL=SUPPORT_EMAIL)
        send_email("Your password has been changed", message, COMMS_EMAIL, [user['email']])
        return redirect(url_for("homepage"))  # TODO Change this when the profile/settings page is made


@app.route('/logout', methods=['GET'])
def logoutpage():
    session.pop('email', None)
    return redirect(url_for('homepage'))


@app.route("/dashboard/buyer", methods=['GET'])
@login_required
def buyerdashboard():
    raise NotImplementedError()


@app.route("/dashboard/seller", methods=['GET'])
@login_required
def sellerdashboard():
    raise NotImplementedError()


@app.route("/dashboard/admin", methods=['GET'])
@login_required
@admin_only
def admindashboard():
    raise NotImplementedError()


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


if __name__ == '__main__':
    app.run(debug=True)

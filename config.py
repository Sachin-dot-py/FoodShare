WEBSITE_BASE_URL = "http://127.0.0.1:5000"  # To change in production

ALLOWED_FILE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif')
EMAIL_REGEX = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'  # Regex for email validation
UPLOADS_FOLDER = "uploads"

COMMS_EMAIL = "FoodShare31@gmail.com"
SUPPORT_EMAIL = "FoodShare31@gmail.com"

WELCOME_TEMPLATE = """
Hi {fname},
<br><br>
Welcome to FoodShare and thanks for joining!
<br><br>
Regards,
<br>
The <i>FoodShare</i> Team
"""

RESET_PASSWORD_TEMPLATE = """ 	
Hi {fname},
<br><br>
To reset your FoodShare account password, please click the link below.
<br><br>
<a href="{link}">RESET PASSWORD</a>
<br><br>
For your security, this reset link will expire shortly and can only be used once.
<br><br>
If you did not request a password reset, please contact us at <a href="mailto:{SUPPORT_EMAIL}">{SUPPORT_EMAIL}</a>.
<br><br>
Regards,
<br>
The <i>FoodShare</i> Team
"""

RESET_PASSWORD_NOTIFICATION = """ 	
Hi {fname},
<br><br>
This is to notify you that your FoodShare account password <b>has been reset</b>. 
<br><br>
If you did not perform this reset, please contact us <b>immediately</b> at <a href="mailto:{SUPPORT_EMAIL}">{SUPPORT_EMAIL}</a>.
<br><br>
Regards,
<br>
The <i>FoodShare</i> Team
"""

CHANGE_PASS_NOTIF = """ 	
Hi {fname},
<br><br>
This is to notify you that your FoodShare account password <b>has been changed</b>. 
<br><br>
If you did not perform this action, please contact us <b>immediately</b> at <a href="mailto:{SUPPORT_EMAIL}">{SUPPORT_EMAIL}</a>.
<br><br>
Regards,
<br>
The <i>FoodShare</i> Team
"""

ORDER_CONFIRM_BUYER = """
Hi {fname},
<br><br>
This is to notify you that your order <b>#{orderid}</b> has been confirmed.
<br><br>
You can view the order details and status <a href="{link}">here</a>.
<br><br>
You will also receive an email once your order is ready for collection.
<br><br>
Regards,
<br>
The <i>FoodShare</i> Team
"""

ORDER_CONFIRM_SELLER = """
Hi {fname},
<br><br>
This is to notify you that you have a new order <b>#{orderid}</b>.
<br><br>
<h2>Order Details</h2>
<table border=1>
<tr><td>Buyer</td><td>{buyer}</td></tr>
<tr><td>Amount</td><td>${amount}</td></tr>
</table>
<br><br>
You can view the order details and update its status <a href="{link}">here</a>.
<br><br>
Regards,
<br>
The <i>FoodShare</i> Team
"""

ORDER_CANCELLED_BY_BUYER = """
Hi,
<br><br>
This is to notify you that your order <b>#{orderid}</b> has been cancelled by the buyer, {buyer}.
<br><br>
Regards,
<br>
The <i>FoodShare</i> Team
"""

ORDER_CANCELLED_BY_SELLER = """
Hi,
<br><br>
This is to notify you that your order <b>#{orderid}</b> has been cancelled by the restaurant, {restaurant}.
<br><br>
Regards,
<br>
The <i>FoodShare</i> Team
"""

ORDER_READY_FOR_COLLECTION = """
Hi,
<br><br>
This is to notify you that your order <b>#{orderid}</b> is ready for collection.
<br><br>
Please proceed to the below restaurant to collect your order.
<br><br>
{restaurant}
<br>
{address}
<br><br>
Regards,
<br>
The <i>FoodShare</i> Team
"""

CONTACT_US_RESPONSE = """
Hi Admin,
<br><br>
You have received a new {nature} from {fname} {lname} ({email}).
<br><br>
{message}
<br><br>
Regards,
<br>
The <i>FoodShare</i> Team
"""

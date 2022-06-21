WEBSITE_BASE_URL = "http://127.0.0.1:5000"  # To change in production

COMMS_EMAIL = "no-reply@FoodShare.xyz"
SUPPORT_EMAIL = "support@FoodShare.xyz"

WELCOME_TEMPLATE = """
Hi {fname},
<br><br>
Welcome to FoodShare and thanks for joining!
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
FoodShare"""

RESET_PASSWORD_NOTIFICATION = """ 	
Hi {fname},
<br><br>
This is to notify you that your FoodShare account password <b>has been reset</b>. 
<br><br>
If you did not perform this reset, please contact us <b>immediately</b> at <a href="mailto:{SUPPORT_EMAIL}">{SUPPORT_EMAIL}</a>.
<br><br>
Regards,
<br>
FoodShare"""

CHANGE_PASS_NOTIF = """ 	
Hi {fname},
<br><br>
This is to notify you that your FoodShare account password <b>has been changed</b>. 
<br><br>
If you did not perform this action, please contact us <b>immediately</b> at <a href="mailto:{SUPPORT_EMAIL}">{SUPPORT_EMAIL}</a>.
<br><br>
Regards,
<br>
FoodShare"""

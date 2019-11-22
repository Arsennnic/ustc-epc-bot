import smtplib, email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.header import Header


class EmailSender:
    SUBJECT = "EPC-Bot Report"
    SMTP = None
    USERNAME = None
    PASSWORD = None

    def __init__(self, username, password):
        self.SMTP = username.split("@")[1]
        self.USERNAME = username
        self.PASSWORD = password

    def send(self, text):
        msg = MIMEMultipart("mixed")
        msg["Subject"] = self.SUBJECT
        msg["From"] = self.USERNAME
        msg["To"] = self.USERNAME
        text = MIMEText(text, "html", "utf-8")
        msg.attach(text)
        smtp = smtplib.SMTP()
        smtp.connect(self.SMTP)
        smtp.login(self.USERNAME, self.PASSWORD)
        smtp.sendmail(self.USERNAME, self.USERNAME, msg.as_string())
        smtp.quit()
    
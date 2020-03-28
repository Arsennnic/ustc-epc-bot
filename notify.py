import winsound
import smtplib, email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.header import Header
from win10toast import ToastNotifier


class EmailSender:

    def __init__(self, addr, pwd):
        self.smtp = addr.split("@")[1]
        self.addr = addr
        self.pwd  = pwd

    def send(self, subject, content):
        msg = MIMEMultipart("mixed")
        msg["Subject"] = subject
        msg["From"]    = self.addr
        msg["To"]      = self.addr
        text = MIMEText(content, "html", "utf-8")
        msg.attach(text)
        smtp = smtplib.SMTP()
        smtp.connect(self.smtp)
        smtp.login(self.addr, self.pwd)
        smtp.sendmail(self.addr, self.addr, msg.as_string())
        smtp.quit()


class DesktopToaster(ToastNotifier):

    def on_destroy(self, hwnd, msg, wparam, lparam):
        pass

    def toast(self, subject, content):
        self.show_toast(subject, content, icon_path="python.ico", threaded=True)
        winsound.PlaySound("chirp.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)

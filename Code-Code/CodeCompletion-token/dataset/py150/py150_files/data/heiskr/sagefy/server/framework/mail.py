from email.mime.text import MIMEText
from smtplib import SMTP

config = {
    'mail_sender': 'support@example.com',
    'mail_password': 'wW6Yd6jJHBVilJHX',
    'mail_username': 'admin@example.com',
    'mail_server': 'smtp.sparkpostmail.com',
    'mail_port': 587,
    'test': False,
}


def send_mail(subject, recipient, body):
    """
    Send an email.
    """

    if config['test']:
        return True

    sent = False
    msg = MIMEText(body, 'plain')
    msg['Subject'] = subject
    msg['From'] = config['mail_sender']
    msg['To'] = recipient
    try:
        conn = SMTP(config['mail_server'], config['mail_port'])
        conn.set_debuglevel(False)
        conn.login(config['mail_username'], config['mail_password'])
        conn.sendmail(msg['To'], [recipient], msg.as_string())
        sent = True
    finally:
        if conn:
            conn.close()
        return sent

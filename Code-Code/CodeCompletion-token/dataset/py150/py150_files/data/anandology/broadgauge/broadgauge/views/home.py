import web
import datetime

from .. import account
from .. import forms
from ..models import Workshop
from ..sendmail import sendmail_with_template
from ..template import render_template

urls = (
    "/", "home",
    "/dashboard", "dashboard",
    "/contact", "contact"
)

class home:
    def GET(self):
        user = account.get_current_user()
        if user:
            raise web.seeother("/dashboard")
        else:
            pending_workshops = Workshop.findall(status='pending', order='date')
            upcoming_workshops = Workshop.findall(status='confirmed', order='date')
            completed_workshops = Workshop.findall(status='completed', order='date desc')

            pending_workshops = [w for w in pending_workshops if w.date >= datetime.date.today()]

            return render_template("home.html",
                pending_workshops=pending_workshops,
                upcoming_workshops=upcoming_workshops,
                completed_workshops=completed_workshops)


class dashboard:
    def GET(self):
        user = account.get_current_user()
        if not user:
            raise web.seeother("/")
        pending_workshops = Workshop.findall(status='pending', order='date')
        pending_workshops = [w for w in pending_workshops if w.date >= datetime.date.today()]

        upcoming_workshops = Workshop.findall(status='confirmed', trainer_id=user.id)
        return render_template("dashboard.html",
                               pending_workshops=pending_workshops,
                               upcoming_workshops=upcoming_workshops)


class contact:
    def GET(self):
        form = forms.ContactForm()
        user = account.get_current_user()
        if user:
            form.email.data = user.email
        return render_template("contact.html", form=form)

    def POST(self):
        i = web.input()
        form = forms.ContactForm(i)
        if form.validate():
            sendmail_with_template("emails/contact.html",
                to=web.config.contact_email,
                subject=form.subject.data,
                message=form.message.data,
                headers={'Reply-To': form.email.data})
            return render_template("message.html",
                title="Sent!",
                message="Thank you for contacting us. We'll get back to you shortly.")
        else:
            return render_template("contact.html", form=form)

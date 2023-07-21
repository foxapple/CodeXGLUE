import os
import logging
import celery
from celery.decorators import task
from celery.signals import task_postrun, task_prerun, task_failure, worker_process_init

from sqlalchemy.exc import IntegrityError, DataError, InvalidRequestError

from totalimpactwebapp.profile import Profile
from totalimpactwebapp import db
from totalimpactwebapp.json_sqlalchemy import JSONAlchemy
from totalimpactwebapp.cards_factory import *
from totalimpactwebapp import notification_report
from totalimpactwebapp import tng_report
from totalimpactwebapp.drip_email import drip_email_context
import emailer


logger = logging.getLogger("ti.tasks")





@task_postrun.connect()
def task_postrun_handler(*args, **kwargs):    
    # close db session
    db.session.remove()


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **kwds):
    try:
        logger.error(u"Celery task FAILED on task_id={task_id}, {args}".format(
            task_id=task_id, args=args))
    except KeyError:
        pass




class TaskAlertIfFail(celery.Task):

    def __call__(self, *args, **kwargs):
        """In celery task this function call the run method, here you can
        set some environment variable before the run of the task"""
        # logger.info(u"Starting to run")
        return self.run(*args, **kwargs)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        if not "profile_id" in args:
            profile_id = "unknown"
        logger.error(u"Celery task failed on {task_name}, profile {profile_id}, task_id={task_id}".format(
            task_name=self.name, profile_id=profile_id, task_id=task_id))




@task(ignore_result=True)
def deduplicate(profile_id):
    profile = Profile.query.get(profile_id)

    removed_tiids = []
    try:
        removed_tiids = profile.remove_duplicates()
        logger.debug(removed_tiids)
    except Exception as e:
        logger.warning(u"EXCEPTION!!!!!!!!!!!!!!!! deduplicating")

    return removed_tiids


@task(base=TaskAlertIfFail)
def send_email_if_new_diffs(profile):

    # profile = db.session.query(Profile).get(profile_id)

    status = "started"
    now = datetime.datetime.utcnow()    
    latest_diff_timestamp = profile.latest_diff_ts
    if not latest_diff_timestamp:
        status = "no diff timestamp"
        return status

    status = "checking diffs"

    if (not profile.last_email_check) or (latest_diff_timestamp > profile.last_email_check):
        # logger.info(u"has diffs since last email check! calling send_email report for {url_slug}".format(url_slug=profile.url_slug))
        status = send_email_report(profile, now)
    else:
        # logger.info(u"not sending, no new diffs since last email sent for {url_slug}".format(url_slug=profile.url_slug))
        status = "no new diffs"

    # set last email check date
    db.session.merge(profile)
    profile.last_email_check = now
    try:
        db.session.commit()
        # logger.info(u"updated profile object in send_email_if_new_diffs for {url_slug}".format(url_slug=profile.url_slug))
    except InvalidRequestError:
        logger.info(u"rollback, trying again to update profile object in send_email_if_new_diffs for {url_slug}".format(url_slug=profile.url_slug))
        db.session.rollback()
        db.session.commit()
        logger.info(u"after rollback updated profile object in send_email_if_new_diffs for {url_slug}".format(url_slug=profile.url_slug))

    return status


def send_tng_email(profile, now=None):
    print "at top of send_tng_email"
    status = "started"
    if not now:
        now = datetime.datetime.utcnow()

    if os.getenv("ENVIRONMENT", "testing") == "production":
        email = profile.email
    else:
        email = "heather@impactstory.org"
    profile.last_email_sent = now
    db.session.merge(profile)

    try:
        db.session.commit()
    except InvalidRequestError:
        logger.info(u"rollback, trying again to update profile object in send_email_report for {url_slug}".format(url_slug=profile.url_slug))
        db.session.rollback()
        db.session.commit()

    print "here now"

    report = tng_report.make(profile)
    if report["profile"]:

        if profile.is_live:
            if profile.orcid_id:
                msg = emailer.send(email, "News about live Impactstory; you have an orcid", "tng_announcement", report)
            else:
                msg = emailer.send(email, "News about live Impactstory; you don't have an orcid", "tng_announcement", report)
        else:
            if profile.orcid_id:
                msg = emailer.send(email, "News about trial Impactstory; you have an orcid", "tng_announcement", report)
            else:
                msg = emailer.send(email, "News about trial Impactstory; you don't have an orcid", "tng_announcement", report)

    status = "email sent"
    logger.info(u"SENT EMAIL to {url_slug}!!".format(url_slug=profile.url_slug))

    return status



def send_email_report(profile, now=None):
    status = "started"
    if not now:
        now = datetime.datetime.utcnow()
    db.session.merge(profile)
    report = notification_report.make(profile)

    if report["cards"]:
        if os.getenv("ENVIRONMENT", "testing") == "production":
            email = profile.email
        else:
            email = "heather@impactstory.org"
        profile.last_email_sent = now

        try:
            db.session.commit()
        except InvalidRequestError:
            logger.info(u"rollback, trying again to update profile object in send_email_report for {url_slug}".format(url_slug=profile.url_slug))
            db.session.rollback()
            db.session.commit()

        msg = emailer.send(email, "Your latest research impacts", "report", report)
        status = "email sent"
        logger.info(u"SENT EMAIL to {url_slug}!!".format(url_slug=profile.url_slug))
    else:
        status = "not emailed, no cards made"
        # logger.info(u"not sending email, no cards made for {url_slug}".format(url_slug=profile.url_slug))

    return status


def send_drip_email(profile, drip_milestone):
    status = "started"    
    if os.getenv("ENVIRONMENT", "testing") == "production":
        email = profile.email
    else:
        email = "heather@impactstory.org"

    email_context = drip_email_context(profile, drip_milestone)
    msg = emailer.send(email, email_context["subject"], email_context["template"], email_context)
    status = "email sent"    
    logger.info(u"SENT EMAIL to {url_slug}!!".format(url_slug=profile.url_slug))

    return status



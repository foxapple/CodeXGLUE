from celery import task
from django.template.loader import render_to_string
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, EmailMessage
from accounts.models import User
from offers.models import Comment, Offer, Like


def advanced_render_to_string(template_name, dictionary, context_instance=None):
    context = dictionary

    if settings.SITE_URL.endswith('/'):
        site_url = 'http://' + settings.SITE_URL[:-1]
    else:
        site_url = 'http://' + settings.SITE_URL

    context.update({"site_url": site_url})

    return render_to_string(template_name, context, context_instance)


@task()
def send_mail(subject, message, message_plain, to):
    msg = EmailMultiAlternatives(
        subject,
        message_plain,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to]
    )
    msg.attach_alternative(
        message,
        "text/html"
    )
    msg.send()


@task()
def send_plain_mail(subject, message, to):
    email = EmailMessage(subject=subject, body=message, from_email=settings.DEFAULT_FROM_EMAIL, to=[to])
    email.send()


@task()
def send_comment_mail(comment_pk):
    if not Comment.objects.filter(pk=comment_pk).exists():
        return

    comment = Comment.objects.get(pk=comment_pk)

    if comment.reply_to is None:
        return

    context = {"comment": comment}

    message = advanced_render_to_string('offers/email/comment_reply.html', context)
    message_plain = advanced_render_to_string('offers/email/comment_reply_plain.txt', context)

    send_mail(
        subject='New reply to your comment',
        message=message,
        message_plain=message_plain,
        to=comment.reply_to.commenter.email
    )

@task()
def send_new_comment_followers_mail(comment_pk, user_pk=None):
    if not Comment.objects.filter(pk=comment_pk).exists():
        return

    current_user = None
    if user_pk is not None:
        current_user = User.objects.get(pk=user_pk)

    comment = Comment.objects.get(pk=comment_pk)
    context = {"comment": comment}

    for countdown, user in enumerate(comment.offer.followers.all()):

        if current_user == user:
            continue

        new_context = context
        new_context.update({"email_user": user})

        message = advanced_render_to_string('offers/email/comment_new.html', new_context)
        message_plain = advanced_render_to_string('offers/email/comment_new_plain.txt', new_context)

        send_mail.s(
            subject=comment.commenter.username + ' replied to an offer you follow!',
            message=message,
            message_plain=message_plain,
            to=user.email,
        ).apply_async(countdown=countdown)


@task()
def publish_latest_offer():
    offers = Offer.objects.filter(status=Offer.REQUEST_COMPLETE).order_by('readied_at')
    if not offers.exists():
        return

    offer = offers[0]
    offer.status = Offer.PUBLISHED

    offer.save()


@task()
def publish_offer(offer_pk):
    offers = Offer.not_requests.filter(pk=offer_pk)
    if not offers.exists():
        return

    offer = offers[0]

    for user_profile in offer.provider.owners.all():
        user = user_profile.user
        offer.followers.add(user)
        send_plain_mail.s(
            'Your offer has been published!',
            advanced_render_to_string('offers/email/provider_offer_published.txt', {"offer": offer, "user": user}),
            user.email
        ).apply_async(countdown=5)


@task()
def send_comment_like(like_pk):
    if not Like.objects.filter(pk=like_pk).exists():
        return
    like = Like.objects.get(pk=like_pk)

    send_plain_mail.s(
        like.user.username + u' has liked your comment!',
        advanced_render_to_string('offers/email/comment_like.txt', {"comment": like.comment, "liker": like.user}),
        like.comment.commenter.email
    ).apply_async()


@task()
def send_comment_unlike(comment_pk, liker_name):
    if not Comment.objects.filter(pk=comment_pk).exists():
        return
    comment = Comment.objects.get(pk=comment_pk)

    send_plain_mail.s(
        liker_name + u' has unliked your comment!',
        advanced_render_to_string('offers/email/comment_unlike.txt', {
            "comment": comment,
            "liker_username": liker_name
        }),
        comment.commenter.email
    ).apply_async()


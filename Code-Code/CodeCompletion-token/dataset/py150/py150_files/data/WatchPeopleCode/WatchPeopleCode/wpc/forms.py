from wpc.models import Subscriber, Streamer, YoutubeChannel, YoutubeStream
from wpc.flask_utils import get_or_create
from utils import youtube_video_id

from flask_wtf import Form
from wtforms import StringField, SubmitField, validators, TextAreaField
from wtforms.validators import ValidationError
from flask.ext.login import current_user

from urlparse import urlparse
import re


def validate_email_unique(form, field):
    email = field.data
    if Subscriber.query.filter_by(email=email).first() is not None:
        raise ValidationError('This email is already in the database.')


class SubscribeForm(Form):
    email = StringField("Email address", [validators.DataRequired(), validators.Email(), validate_email_unique])
    submit_button = SubmitField('Subscribe!')


# TODO: better way
class GLMSubscribeForm(Form):
    email = StringField("Email address", [validators.DataRequired(), validators.Email()])
    submit_button = SubmitField('Subscribe')


class DashboardEmailForm(Form):
    email = StringField("Email address", [validators.DataRequired(), validators.Email()])
    submit_button = SubmitField('Update')

    def prepopulate(self, streamer):
        if streamer.as_subscriber:
            self.email.data = streamer.as_subscriber.email


class DashboardAddVideoForm(Form):
    link = StringField("YouTube link", [validators.DataRequired()])
    submit_button = SubmitField('Add video to the archive')

    def validate_link(form, field):
        ytid = youtube_video_id(field.data)
        if not ytid:
            raise ValidationError("Invalid YouTube URL")

        existing_stream = YoutubeStream.query.filter_by(ytid=ytid).first()
        if existing_stream and existing_stream.streamer:
            raise ValidationError("This video is already added by {}".format(existing_stream.streamer.reddit_username))


class IdeaForm(Form):
    description = TextAreaField("Streamers need your ideas. What kind of streams would you like to see here?", [validators.DataRequired()])
    submit_button = SubmitField('Submit your idea')


class EditStreamTitleForm(Form):
    title = StringField("Title", [validators.Length(max=200)])
    submit_button = SubmitField('Submit')


class RtmpRedirectForm(Form):
    rtmp_redirect_1 = StringField("RTMP Redirect #1")
    rtmp_redirect_2 = StringField("RTMP Redirect #2")
    rtmp_redirect_3 = StringField("RTMP Redirect #3")
    submit_button = SubmitField('Save')

    def prepopulate(self, streamer):
        for rid in xrange(1, 4):
            attrname = 'rtmp_redirect_{}'.format(rid)
            getattr(self, attrname).data = getattr(streamer, attrname)


class EditStreamerInfoForm(Form):
    youtube_channel = StringField("YouTube channel", [validators.Length(max=100)])
    twitch_channel = StringField("Twitch channel", [validators.Length(max=100)])
    info = TextAreaField("Info", [validators.Length(max=5000)])
    submit_button = SubmitField('Submit')

    def twitch_channel_extract(self):
        """
        Examples:
        - channel_name
        - https://www.twitch.tv.channel_name
        - something_wrong?!twitch.tv/channel_name
        """
        string = self.twitch_channel.data.strip()
        position = string.find('twitch.tv')
        if position != -1:
            path = urlparse(string[position:]).path.split('/')
            if len(path) < 2:
                return None
            string = path[1]

        return string if len(string) <= 25 and re.match(r'\w*$', string) else None

    def youtube_channel_extract(self):
        """
        Examples:
        - UCJAVLOqT6Mgn_YD5lAxxkUA
        - https://www.youtube.com/channel/UCJAVLOqT6Mgn_YD5lAxxkUA
        - something_wrong}[youtube.com/channel/UCJAVLOqT6Mgn_YD5lAxxkUA
        """
        string = self.youtube_channel.data.strip()
        position = string.find('youtube.com')
        if position != -1:
            path = urlparse(string[position:]).path.split('/')
            if len(path) < 3 or path[1] != "channel":
                return None
            else:
                string = path[2]

        return string if len(string) == 24 and re.match(r'[\w-]*$', string) or string == '' else None

    def validate_youtube_channel(form, field):
        yc = form.youtube_channel_extract()
        if yc is None:
            # FIXME: add explanation here or hint to page
            raise ValidationError("This field should contain a valid YouTube channel.")

        streamer = get_or_create(YoutubeChannel, channel_id=yc).streamer
        if streamer and streamer.checked and streamer != current_user:
            raise ValidationError("There is another user with this channel. If it is your channel, please message about that to /r/WatchPeoplecode moderators.")

    def validate_twith_channel(form, field):
        tc = form.twitch_channel_extract()
        if tc is None:
            raise ValidationError('This field should contain a valid Twitch channel.')

        streamer = Streamer.query.filter_by(twitch_channel=tc).first()
        if streamer and streamer.checked and streamer != current_user:
            raise ValidationError("There is another user with this channel. If it is your channel, please message about that to /r/WatchPeoplecode moderators.")


class SearchForm(Form):
    query = StringField("Search")
    search_button = SubmitField('Search video archive')

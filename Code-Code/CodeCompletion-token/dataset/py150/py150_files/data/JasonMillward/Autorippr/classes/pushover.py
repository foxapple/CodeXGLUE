"""
Pushover Class


Released under the MIT license
Copyright (c) 2014, Jason Millward

@category   misc
@version    $Id: 1.7-test4, 2015-11-09 12:30:44 ACDT $;
@author     Jason Millward
@license    http://opensource.org/licenses/MIT
"""
import logger
from chump import Application


class Pushover(object):

    def __init__(self, config, debug, silent):
        self.log = logger.Logger("Pushover", debug, silent)
        self.config = config

    def send_notification(self, notification_message):
        app = Application(self.config['app_key'])
        user = app.get_user(self.config['user_key'])
        message = user.send_message(notification_message)

        if message.is_sent:
            self.log.info("Pushover message sent successfully")
        else:
            self.log.error("Pushover message not sent")

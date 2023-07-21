import datetime
import json
from optparse import make_option
import time

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.paginator import Paginator

import tweepy

from ui.models import authenticated_api
from ui.models import TwitterUser
from ui.utils import set_wait_time


class Command(BaseCommand):
    help = 'update any screen names that have changed'
    """
    Cycle through all the TwitterUsers we're tracking and update any
    screen names that have changed.

    see https://dev.twitter.com/docs/api/1.1/get/statuses/user_timeline
      for explanation of user_timeline call
    see https://dev.twitter.com/docs/working-with-timelines
      for explanation of max_id, since_id usage
    see also:
      https://dev.twitter.com/docs/error-codes-responses
      https://dev.twitter.com/docs/rate-limiting
    """

    option_list = BaseCommand.option_list + (
        make_option('--user', action='store', dest='user',
                    default=None, help='Specific user to fetch'),
    )

    def handle(self, *args, **options):
        api = authenticated_api(username=settings.TWITTER_DEFAULT_USERNAME)
        qs_tweeps = TwitterUser.objects.filter(is_active=True)
        if options.get('user', None):
            qs_tweeps = qs_tweeps.filter(name=options.get('user'))
        paginator = Paginator(qs_tweeps, 100)
        page_count = paginator.num_pages
        for page_counter in range(1, page_count + 1):
            print "Page %s of %s" % (page_counter, page_count)
            qs_page = paginator.page(page_counter)
            tweep_map = {}
            for tweep in qs_page:
                # check user status, update twitter user name if it has changed
                if tweep.uid == 0:
                    print 'user: %s' % tweep.name
                    print ' -- uid has not been set yet - skipping.'
                    continue
                else:
                    tweep_map[tweep.uid] = tweep
            if tweep_map:
                try:
                    user_statuses = api.lookup_users(user_ids=tweep_map.keys())
                    for user_status in user_statuses:
                        tweep = tweep_map[user_status['id']]
                        print 'user: %s' % tweep.name
                        if user_status['screen_name'] != tweep.name:
                            print ' -- updating screen name to %s' % \
                                user_status['screen_name']
                            former_names = tweep.former_names
                            if not tweep.former_names:
                                former_names = '{}'
                            oldnames = json.loads(former_names)
                            oldnames[datetime.datetime.utcnow().strftime(
                                '%Y-%m-%dT%H:%M:%SZ')] = tweep.name
                            tweep.former_names = json.dumps(oldnames)
                            tweep.name = user_status['screen_name']
                            #TODO: Is this save unnecessary, since it gets saved below?
                            tweep.save()
                except tweepy.error.TweepError as e:
                    print 'Error: %s' % e
                    #go to the next tweep in the for loop
                    continue
                finally:
                    time.sleep(set_wait_time(api.last_response))

#from https://gist.github.com/scott2b/9219919
# thank you!!

"""
Utilization:
    searcher = TwitterPager(
        TWITTER_CONSUMER_KEY,
        TWITTER_CONSUMER_SECRET,
        TWITTER_APP_CLIENT_ACCESS_TOKEN)
    for query in my_query_generator():
        searcher.paginated_search(
            page_handler=my_page_handler,
            # see birdy AppClient docs and Twitter API docs for params
            # to pass in here:
            since_id=my_since_id,
            q=query,
            count=100,
            lang='en'
        ) 
"""
import logging
import time
import urlparse
from birdy.twitter import AppClient
from birdy.twitter import TwitterRateLimitError, TwitterClientError
from delorean import parse, epoch
import totalimpactwebapp

DEFAULT_MAX_PAGES = 10

# from https://github.com/inueni/birdy/issues/7
# to overrride JSONObject
class AppDictClient(AppClient):
    @staticmethod
    def get_json_object_hook(data):
        return data

class TwitterPager(object):
    """Class to manage searches against the Twitter REST search API.
    Utilizes the birdy AppClient. Handles client reconnection for
    connection pool disconnects. Provides automated pagination.

    Manages the search API rate limit with limit info from the API itself --
    no need to pace your queries, but if using beyond the rate limit, your
    queries will get delayed as needed."""

    def __init__(self, twitter_consumer_key, twitter_consumer_secret,
            twitter_app_client_access_token,
            default_max_pages=DEFAULT_MAX_PAGES):
        self._client = None
        self.consumer_key = twitter_consumer_key
        self.consumer_secret = twitter_consumer_secret
        self.app_client_access_token = twitter_app_client_access_token
        self.default_max_pages = default_max_pages
        self.last_twitter_search = None
        self.rate_limit_remaining = 1
        self.rate_limit_limit = None
        self.rate_limit_reset = None
        self.twitter_date = None
        self.first_request = True

    @property
    def client(self):
        if self._client is None:
            logging.debug('Creating new Twitter client.')
            self._client = AppDictClient(
                self.consumer_key,
                self.consumer_secret,
                access_token=self.app_client_access_token
            )

        return self._client

    def reset_client(self):
        """Forces new HTTP connection session for AppClient."""
        self._client = None

    def extract_rate_limit(self, response):
        """Extract rate limit info from response/headers.
        get it just from the response, so it is relevant to the type of query we are doing"""
        try:
            self.rate_limit_remaining = int(response.headers['x-rate-limit-remaining'])
            self.rate_limit_limit = int(response.headers['x-rate-limit-limit'])
            self.rate_limit_reset = epoch(int(response.headers['x-rate-limit-reset'])).datetime
            self.twitter_date = parse(response.headers['date']).datetime
            logging.debug(
                'Twitter rate limit info:: rate-limit: %s, remaining: %s' % (self.rate_limit_limit, self.rate_limit_remaining))
            # logging.debug(
            #     'Twitter rate limit info:: rate-limit: %s, remaining: %s, '\
            #     'reset: %s, current-time: %s' % (self.rate_limit_limit,
            #     self.rate_limit_remaining, self.rate_limit_reset, self.twitter_date))
        except KeyError:
            pass

    def fetch_rate_limit(self, query_type):
        """Send search rate limit info request to Twitter API."""
        response = self.client.api.application.rate_limit_status.get(
            resources='/statuses/user_timeline')
        self.extract_rate_limit(response)
        return {
            'limit': self.rate_limit_limit,
            'remaining': self.rate_limit_remaining,
            'reset': self.rate_limit_reset
        }

    def wait_for_reset(self):
        """Requires header information to be current."""
        t = (self.rate_limit_reset - self.twitter_date).seconds + 1 # to grow on
        logging.info('Waiting %d seconds for Twitter rate limit reset.' % t)
        time.sleep(t)

    def query(self, **kwargs):
        """Passes kwargs to search.tweets.get of the AppClient.
        For kwargs requirements, see docs for birdy AppClient."""
        query_type = kwargs.get("query_type", "user_timeline")
        if self.first_request:
            self.fetch_rate_limit(query_type)
            self.first_request = False
        if self.rate_limit_remaining <= 0:
            logging.info('Reached Twitter rate limit.')
            self.wait_for_reset()
        try:
            
            if query_type=="user_timeline":
                response = self.client.api.statuses.user_timeline.get(**kwargs)
            elif query_type=="statuses_lookup":
                response = self.client.api.statuses.lookup.post(**kwargs)

            # logging.debug('Received twitter search response')
            self.extract_rate_limit(response)
            return response
        except TwitterRateLimitError, e:
            logging.warning('Twitter rate limit exceeded.')
            # headers = e.headers ## this seems to always be None
            # Birdy does not seem to be attaching headers to the exception
            # object, so we need to get the wait time from Twitter.
            self.fetch_rate_limit(query_type)
            self.wait_for_reset()
            return self.query(**kwargs)
        except TwitterClientError, e:
            # requests library is not propagating connection pool session
            # disconnects. Hence the need to look at the string.
            if str(e).startswith('HTTPSConnectionPool'):
                logging.debug('Connection pool disconnect. Reconnecting.')
                self.reset_client()
                return self.query(**kwargs)
            else:
                raise e

    def paginated_search(self, page=1, page_handler=None,
            max_pages=None, **kwargs):

        """Issue search with AppClient up to max_pages.
        For kwargs requirements, see docs for birdy AppClient."""
        if max_pages is None:
            max_pages = self.default_max_pages

        response = self.query(**kwargs)

        if page_handler:
            has_next_page = page_handler(response)

        if page < max_pages and has_next_page:
            try:
                kwargs.update({ k:v for k,v in urlparse.parse_qsl(
                    response.data.search_metadata.next_results[1:]) })
                if int(kwargs['max_id']) > int(kwargs.get('since_id',0)):
                    # logging.debug('Paginating query: %s' % str(kwargs))
                    self.paginated_search(page=page+1,
                            page_handler=page_handler,
                            max_pages=max_pages, **kwargs)

            except AttributeError:
                try:
                    kwargs['max_id'] = str(response.data[-1]["id"])
                    # logging.debug('Paginating query: %s' % str(kwargs))
                    self.paginated_search(page=page+1,
                            page_handler=page_handler,
                            max_pages=max_pages, **kwargs)
                except (IndexError, TypeError):
                    logging.debug('error paging, so stop')

        else:
            # logging.debug('reached max pages or told no next page, so stop')
            pass
        return response



    
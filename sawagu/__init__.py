# -*- coding: utf-8 -*-
import os
import feedparser
import requests
import tweepy
from configobj import ConfigObj


def main():
    cache = Cache(Settings.CACHE_FILE)
    shortener = Shortener(Settings.SHORTENER_URL)
    tweeter = Tweeter(Settings.TWITTER_CONSUMER_KEY,
            Settings.TWITTER_CONSUMER_SECRET,
            Settings.TWITTER_ACCESS_TOKEN,
            Settings.TWITTER_ACCESS_TOKEN_SECRET)

    response = requests.get(Settings.FEED_URL)
    new_data = response.content
    new_feed = feedparser.parse(new_data)

    last_data = cache.load()
    last_feed = feedparser.parse(last_data)

    new_entries = [x for x in new_feed.entries
            if x.id not in [y.id for y in last_feed.entries]]
    print "Got new entries:", len(new_entries)

    # tweet the oldest entries first
    new_entries.reverse()
    for entry in new_entries:
        message = Message(
                title=entry.title,
                link=shortener.shorten(entry.feedburner_origlink),
                tags=[x.term for x in entry.tags])
        tweeter.send_tweet(unicode(message))

    cache.save(new_data)


class Shortener(object):

    def __init__(self, shortener_url):
        self.shortener_url = shortener_url

    def shorten(self, url):
        if not self.shortener_url:
            return url

        data = {'url': url}
        response = requests.post(self.shortener_url, data=data)
        short_url = response.content.strip()
        return short_url


class Message(object):

    def __init__(self, title='', link='', tags=()):
        self.title = title
        self.link = link
        self.tags = tags

    def __unicode__(self):
        message = self.link

        if len(self.title + message) + 1 > 140:
            title = self.truncate(self.title, u' ' + message)
            message = title + u' ' + message
        else:
            message = self.title + u' ' + message

        for tag in self.tags:
            if len(message + tag) + 2 <= 140:
                message += u" #" + tag

        return message

    def truncate(self, to_shorten, to_keep):
        shorten_by = len(to_shorten + to_keep) - 140 + 1
        result = to_shorten[:shorten_by] + u"…"
        return result


class Cache(object):

    def __init__(self, cache_filename):
        self.cache_filename = cache_filename

    def save(self, data):
        with open(self.cache_filename, 'w') as f:
            f.write(data)

    def load(self):
        try:
            f = open(self.cache_filename, 'r')
        except IOError, e:
            if e.errno != 2:
                raise
            return ''
        else:
            data = f.read()
            f.close()
            return data


class Tweeter(object):

    def __init__(self, consumer_key, consumer_secret,
            access_token, access_token_secret):
        self.auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        self.auth.set_access_token(access_token, access_token_secret)
        self.api = tweepy.API(self.auth)

    def send_tweet(self, message):
        print "Sending message", unicode(message)
        try:
            self.api.update_status(message)
        except tweepy.TweepError, e:
            if 'duplicate' not in str(e):
                raise
            print str(e)


def _get_local_settings():
    default_location = os.environ.get('HOME', '') + "/.sawagu"
    location_from_env = os.environ.get('SAWAGU_SETTINGS')
    
    if location_from_env and os.path.exists(location_from_env):
        return ConfigObj(location_from_env)

    elif os.path.exists(default_location):
        return ConfigObj(default_location)

    else:
        return ConfigObj()


class Settings(object):
    
    __config = _get_local_settings()

    CACHE_FILE = __config.get('CACHE_FILE') or '/tmp/sawagu.xml'
    FEED_URL = __config.get('FEED_URL') or ''
    SHORTENER_URL = __config.get('SHORTENER_URL') or ''
    TWITTER_CONSUMER_KEY = __config.get('TWITTER_CONSUMER_KEY') or ''
    TWITTER_CONSUMER_SECRET = __config.get('TWITTER_CONSUMER_SECRET') or ''
    TWITTER_ACCESS_TOKEN = __config.get('TWITTER_ACCESS_TOKEN') or ''
    TWITTER_ACCESS_TOKEN_SECRET = \
            __config.get('TWITTER_ACCESS_TOKEN_SECRET') or ''


if __name__ == '__main__':
    main()

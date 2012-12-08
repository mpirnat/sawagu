# -*- coding: utf-8 -*-
import feedparser
import requests
import tweepy

from sawagu.settings import Settings


def main():
    settings = Settings()

    cache = Cache(settings.CACHE_FILE)
    shortener = Shortener(settings.SHORTENER_URL)
    tweeter = Tweeter(settings.TWITTER_CONSUMER_KEY,
            settings.TWITTER_CONSUMER_KEY_SECRET,
            settings.TWITTER_ACCESS_TOKEN,
            settings.TWITTER_ACCESS_TOKEN_SECRET)

    response = requests.get(settings.FEED_URL)
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
        print "Want to send message", unicode(message)
#        tweeter.send_tweet(unicode(message))

    cache.save(new_data)


class Shortener(object):

    def __init__(self, shortener_url):
        self.shortener_url = shortener_url

    def shorten(self, url):
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

    def __init__(self, consumer_key, consumer_key_secret,
            access_token, access_token_secret):
        self.auth = tweepy.OAuthHandler(
                consumer_key, consumer_key_secret)
        self.auth.set_access_token(access_token, access_token_secret)
        self.api = tweepy.API(self.auth)

    def send_tweet(self, message):
        #try:
        self.api.update_status(message)
        #except tweepy.TweepError:
        #    pass


if __name__ == '__main__':
    main()

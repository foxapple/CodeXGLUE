"""
abuse.ch Zeus C&C RSS feed bot.

Maintainer: Lari Huttunen <mit-code@huttu.net>
"""

import re
from abusehelper.core import bot

from . import host_or_ip, resolve_level, split_description, AbuseCHFeedBot


class ZeusCcBot(AbuseCHFeedBot):
    feed_malware = "zeus"
    feed_type = "c&c"

    feeds = bot.ListParam(default=["https://zeustracker.abuse.ch/rss.php"])

    def parse_title(self, title):
        pieces = title.split(None, 1)

        yield host_or_ip(pieces[0])

        if len(pieces) > 1:
            date = pieces[1]
            date = re.sub("[()]", "", date)
            yield "source time", date + "Z"

    def parse_description(self, description):
        for key, value in split_description(description):
            if key == "status":
                yield key, value
            elif key == "level":
                yield "description", resolve_level(value)
            elif key == "sbl" and value.lower() != "not listed":
                yield key + " id", value
            elif key == "ip address":
                yield "ip", value

if __name__ == "__main__":
    ZeusCcBot.from_command_line().execute()

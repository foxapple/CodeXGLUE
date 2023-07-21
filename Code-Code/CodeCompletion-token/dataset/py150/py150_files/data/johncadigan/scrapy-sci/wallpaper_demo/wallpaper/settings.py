# -*- coding: utf-8 -*-

# Scrapy settings for wallpaper project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'wallpaper'

SPIDER_MODULES = ['wallpaper.spiders']
NEWSPIDER_MODULE = 'wallpaper.spiders'
DOWNLOAD_DELAY = 2
COOKIES_ENABLED = False
AUTOTHROTTLE_ENABLED = True
ITEM_PIPELINES = {'wallpaper.duplicate_pipeline.DuplicatesPipeline': 100,
		  'wallpaper.classifier_pipelines.ClassifiersPipeline': 200,}
COMMANDS_MODULE = 'scrapy_sci.commands'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'wallpaper (+http://www.yourdomain.com)'

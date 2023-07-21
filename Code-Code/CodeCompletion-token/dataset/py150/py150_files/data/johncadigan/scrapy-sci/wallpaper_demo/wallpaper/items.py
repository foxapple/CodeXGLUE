# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
import webbrowser
import threading


class Wallpaper(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    origin = scrapy.Field()
    id = scrapy.Field()
    uploader = scrapy.Field()
    site = scrapy.Field()
    favorites = scrapy.Field()
    views = scrapy.Field()    
    download_link = scrapy.Field()
    filetype = scrapy.Field()
    colors = scrapy.Field()
    x_resolution = scrapy.Field()
    y_resolution = scrapy.Field()    
    descriptors = scrapy.Field()
    comments = scrapy.Field()
    
    
    @classmethod
    def review(self,dic):
        x=lambda: webbrowser.open_new(dic['origin'])
        t=threading.Thread(target=x)
        t.start()
    


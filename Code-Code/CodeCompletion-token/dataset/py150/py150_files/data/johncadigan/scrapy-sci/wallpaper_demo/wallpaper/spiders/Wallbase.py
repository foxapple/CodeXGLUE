from wallpaper.items import Wallpaper
import re
import scrapy
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors import LinkExtractor



class WallbaseSearch(CrawlSpider):
    name = "wallbase"
    allowed_domains = ["http://wallbase.cc/", "wallbase.cc"]
    start_urls = [
    "http://wallbase.cc/random"
    ]
    rules = (

    Rule(LinkExtractor(
            allow=('http://wallbase.cc/wallpaper/[0-9]*', )
        ), callback='parse_wallpaper'),

    )

    def parse_wallpaper(self, response):
        wallpaper = Wallpaper()
        wallpaper['uploader'] = response.xpath('//a[contains(@class, "user-link")]/text()').extract()[0]
        wallpaper['site'] = "wallbase.cc"
        wallpaper['origin'] = response.url
        wallpaper['favorites'] = int(response.xpath('//div[contains(@class, "favsrow")]/div[contains(@class, "title")]/span/text()').extract()[0])
        wallpaper['views'] = int("".join(response.xpath('//div[contains(@class, "centr")]/div[contains(@class, "l1")]//span[contains(@class, "highl")]/text()').extract()[0].split(",")))
        wallpaper['download_link'] = response.xpath('//div[contains(@class, "content")]/img[contains(@class, "wall")]/@src').extract()[0]
        colors = response.xpath('//div[contains(@class, "palette")]/a/@style').extract()
        wallpaper['filetype'] = wallpaper['download_link'].split('.')[-1] #get the last item
        wallpaper['colors'] = ["#" + hex[0:-1] for n, hex in [color.split('#') for color in colors]] #-1 removes semi-colon
        res = response.xpath('//a[contains(@class, "reso")]/div[contains(@class, "l1")]/text()').extract()[0]
        wallpaper['x_resolution'] = int(res.split('x')[0])
        wallpaper['y_resolution'] = int(res.split('x')[1])
        wallpaper['descriptors'] = response.xpath('//ul[contains(@class, "taglist")]/li[contains(@class, "item")]/a/text()').extract()
        wallpaper['comments'] = [""] 
        yield wallpaper  
 

#!/usr/bin/env python
import webapp2
import feedparser
import re

import time

from google.appengine.api.images import Image
from google.appengine.api import urlfetch

weightPhil = 45
avgBeerSize = 33 # in cl
avgBeerAlcoholPercentage = 5 # in percentage
alcoholBeer = avgBeerSize * avgBeerAlcoholPercentage * 0.08

promilToWords = {3:"was nearly not drunk", 5:"was a bit drunk", 8:"did started to get a bit slow", 10:"had to search for words",
                15: "was quite drunk", 20:"had to throw up", 25: "had to go to the hospital", 30: "couldn't stand anymore", 40:"died"}

class MainHandler(webapp2.RequestHandler):
    def get(self):
        url = "http://eatingstats.tumblr.com/tagged/beer/rss"

        d = feedparser.parse(url)
        
        articles = []
        lastbeer = None
        lastbeerPic = ""
        beers = []
        promile = 0
        
        self.response.out.write("<!--")
        for row in d.entries:
            article = row['description'].encode('utf-8');
            pictureUrl = re.search("(?P<url>https?://[^\s\"]+)", article).group("url")
            result = urlfetch.fetch(pictureUrl)
            if result.status_code == 200:
                img = Image(image_data=result.content);
                img.rotate(0)
                img.execute_transforms(parse_source_metadata=True)
                meta = img.get_original_metadata()
                self.response.out.write(meta)
                if 'DateCreated' in meta:
                    #date like 2012:07:18 17:35:56
                    date = time.strptime(meta['DateCreated'], "%Y:%m:%d %H:%M:%S")
                    self.response.out.write(date)
                    if lastbeer == None:
                        lastbeer = date
                        lastbeerPic = pictureUrl
                        promile += alcoholBeer / (0.7*weightPhil)
                    else:
                        delta = abs(time.mktime(lastbeer) - time.mktime(date))
                        self.response.out.write("since the last beer: "+str(delta))
                        if delta > 12 * 60 * 60:
                            break;
                        promile += alcoholBeer / (0.7*weightPhil)
                        if delta > 2 * 60 * 60:
                            timeToReduceAlcohol = (delta - 2 * 60 * 60) #for two hours there will be no reduction of blood alcohol content
                            reducedAlcoholByHourInGram = 0.1 * weightPhil
                            reducedAlcoholSinceLastBeer = delta/3600 * reducedAlcoholByHourInGram * 0.08
                            if reducedAlcoholSinceLastBeer <  alcoholBeer / (0.7*weightPhil):
                                promile += alcoholBeer / (0.7*weightPhil) - reducedAlcoholSinceLastBeer
                    
                    self.response.out.write("current promille: "+str(promile))
                    beers.append(date)
            articles.append(pictureUrl)	
        
        self.response.out.write("-->")

        word = ""
        for k,v in sorted(promilToWords.items()):
            if k > promile * 10 :
                word = v
                break
        
        self.response.out.write("<center><h1>Phil "+word+"!</h1>")
        self.response.out.write("<p>"+time.strftime('At the %d, %h %Y',beers[0])+" with "+str(round(promile/10, 4))+" percent <a href=\"http://en.wikipedia.org/wiki/Blood_alcohol_content\">blood alcohol content.</a></p>")
        self.response.out.write("<br /><img src=\""+lastbeerPic+"\" alt=\"last beer of phil\" /></center>")
        self.response.out.write("<a href=\"https://github.com/you\"><img style=\"position: absolute; top: 0; right: 0; border: 0;\" src=\"https://s3.amazonaws.com/github/ribbons/forkme_right_darkblue_121621.png\" alt=\"Fork me on GitHub\"></a>")

app = webapp2.WSGIApplication([('/', MainHandler)], debug=True)
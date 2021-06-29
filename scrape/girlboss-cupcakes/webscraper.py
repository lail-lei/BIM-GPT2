import re
import csv
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
import nltk
nltk.download('punkt')


class GirlBossParser ():
    
    def _init_ (self):
        self.title = ""
        self.tags = []
        self.ingredients = []
        self.steps = []
        self.yields = None
        self.soup = None
        self.url = None
    
    def makeSoup (self):
        # make request to disguise scraping
        req = Request(self.url, headers={'User-Agent': 'Mozilla/5.0'})
        webpage = urlopen(req).read()
        self.soup = BeautifulSoup(webpage, "html.parser")
        
    def parseIngredients (self, list):
        ingredients = []
        for item in list:
            ingredient_object = {}
            if item.find("span"):
                if item.find("span").has_attr('data-amount'):
                    ingredient_object["amount"] = item.find("span")["data-amount"]
                if item.find("span").has_attr('data-unit'):
                    ingredient_object["unit"] = item.find("span")["data-unit"]
                    
            text = re.sub(r'\([^)]*\)', ' ', item.text) # get rid of parentheticals (items within parens and parens)
            ingredient_object["text"] = re.sub(r"[^a-zA-Z0-9/().]+", ' ', text) # get rid of special characters
            ingredients.append(ingredient_object)
            
        return ingredients
        
    
    def parseSteps (self, list):
        steps = []
        for item in list:
            text = re.sub("^[0-9].|^\n|^\n1.", "", item.text)
            text = re.sub(r"[^a-zA-Z0-9.,()/\-]+", ' ', text)
            text = text.strip()
            list = nltk.tokenize.sent_tokenize(text)
            for sentence in list:
                steps.append(sentence)
        return steps
        

    def isolateTag (self, text):
        rep = {"category": "", "tag": "", "-": " "}
        rep = dict((re.escape(k), v) for k, v in rep.items())
        pattern = re.compile("|".join(rep.keys()))
        return pattern.sub(lambda m: rep[re.escape(m.group(0))], text)

    def parseTags (self, html):
     
        prefixes=("category", "tag") # these are our tag classes
        list = html["class"]
        tags = [x for x in list if x.startswith(prefixes)]
        # now tags only has category- and tag- classes
        for index, tag in enumerate(tags):
            tags[index] = self.isolateTag(tag)

        return tags
        
    def isRecipe (self):
       return self.soup.select(".tasty-recipes-ingredients-body li") != None and self.soup.find("div", {"class": "tasty-recipes-instructions-body"}) != None
    
        
    def parse (self):
        # can't parse if isnt a recipe
        if self.isRecipe() == False:
            return False
        self.title = self.soup.find("h1", {"class": "infinite-single-article-title"}).text
        serves = self.soup.find("span", {"class": "tasty-recipes-yield"})
        # remove extra text
        if serves:
        
            processed = re.sub("1x *$", "", serves.text)
            self.yields = processed
        else:
            self.yields = "12 cupcakes" #replace missing yield with common yield
        self.ingredients = self.parseIngredients(self.soup.select(".tasty-recipes-ingredients-body li"))
        # some steps are li, some are p, some are div
        raw_steps = self.soup.select(".tasty-recipes-instructions-body li")
        if len(raw_steps) == 0:
            raw_steps = self.soup.select(".tasty-recipes-instructions-body p")
            if len(raw_steps) == 0:
                raw_steps = self.soup.select(".tasty-recipes-instructions-body div")
        self.steps = self.parseSteps(raw_steps)
        self.tags = self.parseTags(self.soup.find("article", {"class": "post"}))
        # parsed successfully
        return True
        
    #json
    def getJSON (self):
        json = {}
        json["title"] = self.title
        json["yield"] = self.yields
        json["ingredients"] = self.ingredients
        json["steps"] = self.steps
        json["url"] = self.url
        json["tags"] = self.tags
        return json
        
        
    def run (self, url):
        self.url = url
        self.makeSoup()
        return self.parse()



class GirlBossSpider:

  # hosts all cupcake recipes on the site
  directory = "https://www.lifeloveandsugar.com/page/"
  search = "/?s=cupcakes"
  
  links = [] # resulting list of links from scrape
  parser = GirlBossParser()
  
  def _init_ (self):
    self.soup = None
    
  
  def makeSoup (self, page):
    # make request to disguise scraping
    url = self.directory + str(page) + self.search;
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    self.soup = BeautifulSoup(webpage, "html.parser")
    
  def consumeSoup (self):
    library = self.soup.select('.gdlr-core-blog-thumbnail a', recursive=False)
    for element in library:
        self.links.append(element['href'])
      
  # keep copy of urls scraped
  def parseAndWriteLinks (self):
    with open('cupcakes.csv', mode='a') as recipe_file:
        writer = csv.writer(recipe_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for index in range(len(self.links)):
            # run parser on url
            # if parsed object exists
            if self.parser.run(self.links[index]) == True:
                # get parsed object
                json = self.parser.getJSON()
                # write to csv
                writer.writerow([json["title"], json["yield"], json["ingredients"], json["steps"], json["url"], json["tags"]])
    recipe_file.close()
    
 
 
  def run (self):
    for page in range(1, 6):
        self.makeSoup(page)
        self.consumeSoup()
    self.parseAndWriteLinks()
  

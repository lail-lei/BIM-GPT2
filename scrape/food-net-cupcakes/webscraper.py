import re
import csv
from bs4 import BeautifulSoup
from selenium import webdriver
from urllib.request import Request, urlopen
import nltk
nltk.download('punkt')

    

class FoodParser ():
    
    
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
   
    def parseTitle (self):
        if self.soup.find("h1") == None:
            return False
        self.title = self.soup.find("h1", {"class": "o-AssetTitle__a-Headline"}).text.strip()
        return True
    
    def processText (self, text):
        text = re.sub(r'\([^)]*\)', ' ', text) # get rid of parentheticals (items within parens and parens)
        text = re.sub(r"[^a-zA-Z0-9/().]+", ' ', text) # get rid of special characters
        return text.strip()
    
        
    def parseIngredients (self):
        list = self.soup.select(".o-Ingredients__a-Ingredient")
        if len(list) == 0:
            return False
        list.pop(0) # remove first item (recipe noise)
        self.ingredients = [{"text": self.processText(item.text)} for item in list]
        return True
    
    def parseSteps (self):
        list = self.soup.select(".o-Method__m-Step")
        if len(list) == 0:
            return False
        steps = [self.processText(item.text) for item in list]
        self.steps = steps
        return True
    
    def parseYield (self):
        yields = self.soup.select(".o-RecipeInfo__m-Yield li .o-RecipeInfo__a-Description")
        if yields == None or len(yields) == 0:
            self.yields = "12"
        else:
           self.yields = yields[0].text
           

    def parseTags (self):
        tags = self.soup.select(".o-Capsule__m-TagList a")
        for index, tag in enumerate(tags):
            tags[index] = tag.text
        self.tags = tags
        
 
           
    def parse (self):
        
        if self.parseTitle() == False:
            return False
        if self.parseIngredients() == False:
            return False
        if self.parseSteps() == False:
            return False
        
        # non essential fields below
        self.parseYield() # fills in with most common
        self.parseTags()
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
        



class FoodSpider:

  # hosts all cupcake recipes on the site
  directory = "https://www.foodnetwork.com/search/cupcakes-/p/";
  query = "/CUSTOM_FACET:RECIPE_FACET"
  links = [] # resulting list of links from scrape
  parser = FoodParser()
  
  def _init_ (self):
    self.soup = None
    
  
  def makeSoup (self, page):
    # make request to disguise scraping
    url = self.directory + str(page) + self.query;
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    self.soup = BeautifulSoup(webpage, "html.parser")
    
  def consumeSoup (self):
    library = self.soup.select(".o-ResultCard__m-MediaBlock .m-MediaBlock__m-TextWrap .m-MediaBlock__a-Headline a")
    for element in library:
        self.links.append("https:"+element['href'])
      
  # keep copy of urls scraped
  def parseAndWriteLinks (self):
    with open('cupcakes.csv', mode='a') as recipe_file:
        writer = csv.writer(recipe_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for index in range(len(self.links)):
            # run parser on url
            if self.parser.run(self.links[index]) == True:
                # get parsed object
                json = self.parser.getJSON()
                # write to csv
                writer.writerow([json["title"], json["yield"], json["ingredients"], json["steps"], json["url"], json["tags"]])
    recipe_file.close()
    
 
 
  def run (self):
    for page in range(70, 78):
        self.makeSoup(page)
        self.consumeSoup()
    self.parseAndWriteLinks()
  


import re
import csv
from bs4 import BeautifulSoup
from selenium import webdriver
from urllib.request import Request, urlopen
import nltk
nltk.download('punkt')

    

class AmyParser ():
    
    description = ""
    
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
        self.title = self.soup.find("h1", {"class": "entry-title"}).text
        return True
    
    def processText (self, text):
        text = re.sub(r'\([^)]*\)', ' ', text) # get rid of parentheticals (items within parens and parens)
        text = re.sub(r"[^a-zA-Z0-9/().]+", ' ', text) # get rid of special characters
        return text
    
        
    def parseIngredients (self):
        list = self.soup.select(".ingredient")
        if len(list) == 0:
            list = self.soup.select(".wprm-recipe-ingredient")
            if len(list) == 0:
                return False
        # filter out the "for cupcakes"/ "for frosting" messages
        ingredients = []
        for item in list:
            if item.find("span") or item.find("strong"):
                continue
            ingredients.append({"text": self.processText(item.text)})
        self.ingredients = ingredients
        return True
    
    def parseSteps (self):
        list = self.soup.select(".instruction")
        if len(list) == 0:
            list = self.soup.select(".wprm-recipe-instruction")
            if len(list) == 0:
                return False
        steps = [self.processText(item.text) for item in list]
        self.steps = steps
        return True
    
    def parseYield (self):
        yields = self.soup.find("span", {"itemprop": "recipeYield"})
        if yields == None:
            self.yields = "12"
        else:
           self.yields = yields.text
           
    def isolateTag (self, text):
        rep = {"category": "", "tag": "", "-": " "}
        rep = dict((re.escape(k), v) for k, v in rep.items())
        pattern = re.compile("|".join(rep.keys()))
        return pattern.sub(lambda m: rep[re.escape(m.group(0))], text).strip()

    def parseTags (self):
        html = self.soup.find("article", {"class" : "post"})
        prefixes=("category", "tag") # these are our tag classes
        list = html["class"]
        tags = [x for x in list if x.startswith(prefixes)]
        # now tags only has category- and tag- classes
        for index, tag in enumerate(tags):
            tags[index] = self.isolateTag(tag)
        self.tags = tags
        
    def parseDescription (self):
        html = self.soup.find("div", {"itemprop": "description"})
        if html != None:
           self.description = html.text
           
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
        self.parseDescription()
        
        print(self.title)
            
        return True
        
    #json
    def getJSON (self):
        json = {}
        json["title"] = self.title
        json["yield"] = self.yields
        json["ingredients"] = self.ingredients
        json["steps"] = self.steps
        json["url"] = self.url
        json["description"] = self.description
        json["tags"] = self.tags
        return json
        
        
    def run (self, url):
        self.url = url
        self.makeSoup()
        return self.parse()
        



class AmySpider:

  # hosts all cupcake recipes on the site
  directory = "https://amyshealthybaking.com/page/";
  query = "/?id=36906&s=cupcakes"
  links = [] # resulting list of links from scrape
  parser = AmyParser()
  
  def _init_ (self):
    self.soup = None
    
  
  def makeSoup (self, page):
    # make request to disguise scraping
    url = self.directory + str(page) + self.query;
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    self.soup = BeautifulSoup(webpage, "html.parser")
    
  def consumeSoup (self):
    library = self.soup.select("article .entry-image-link")
    for element in library:
        self.links.append(element['href'])
      
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
                writer.writerow([json["title"], json["yield"], json["ingredients"], json["steps"], json["url"], json["tags"], json["description"]])
    recipe_file.close()
    
 
 
  def run (self):
    for page in range(21, 41):
        self.makeSoup(page)
        self.consumeSoup()
    self.parseAndWriteLinks()
  


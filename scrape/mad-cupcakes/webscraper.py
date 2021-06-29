import re
import csv
from bs4 import BeautifulSoup
from selenium import webdriver
from urllib.request import Request, urlopen
import nltk
nltk.download('punkt')

    

class MadParser ():
    
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
        self.title = self.soup.find("h1").text
        return True
    
    def processText (self, text):
        text = re.sub(r'\([^)]*\)', ' ', text) # get rid of parentheticals (items within parens and parens)
        text = re.sub(r"[^a-zA-Z0-9/().]+", ' ', text) # get rid of special characters
        return text
        
    def parseIngredients (self):
        list = self.soup.select(".c-ingredientGroup__item")
        if len(list) == 0:
            return False
        ingredients = [{"text": self.processText(item.text)} for item in list]
        self.ingredients = ingredients
        return True
    
    def parseSteps (self):
        list = self.soup.select(".c-recipeMethod__cmsContent")
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
  
    def parse (self):
        
        if self.parseTitle() == False:
            return False
        if self.parseIngredients() == False:
            return False
        if self.parseSteps() == False:
            return False
        
        # non essential fields below
        self.parseYield() # fills in with most common
            
        return True
        
    #json
    def getJSON (self):
        json = {}
        json["title"] = self.title
        json["yield"] = self.yields
        json["ingredients"] = self.ingredients
        json["steps"] = self.steps
        json["url"] = self.url
        return json
        
        
    def run (self, url):
        self.url = url
        self.makeSoup()
        return self.parse()
        



class MadSpider:

  # hosts all cupcake recipes on the site
  directory = "https://www.bakingmad.com/search/recipes?page=";
  query = "&query=cupcakes"
  
  links = [] # resulting list of links from scrape
  parser = MadParser()
  
  def _init_ (self):
    self.soup = None
    
  def createOptions (self):
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--incognito')
    options.add_argument('--headless')
    return options
  
  
  def makeSoup (self, page):

    url = self.directory + str(page) + self.query;
    driver = webdriver.Chrome(chrome_options=self.createOptions())
    driver.implicitly_wait(3) # seconds
    driver.get(url)
    links = driver.find_elements_by_class_name("c-recipeCard")
    links = [element.get_attribute('href') for element in links]
    self.links = [*self.links, *links]

  
  def parseAndWriteLinks (self):
    with open('cupcakes.csv', mode='a') as recipe_file:
        writer = csv.writer(recipe_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for index in range(len(self.links)):
            if self.parser.run(self.links[index]) == True:
                # get parsed object
                json = self.parser.getJSON()
                #write to csv
                writer.writerow([json["title"], json["yield"], json["ingredients"], json["steps"], json["url"]]) #
    recipe_file.close()
 
  def run (self):
    for page in range(10, 12):
        self.makeSoup(page)
    self.parseAndWriteLinks()
  
  


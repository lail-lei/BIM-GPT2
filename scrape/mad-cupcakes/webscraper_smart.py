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
        text = self.soup.find("h1").text
        text = re.sub(r'(?<=by)', '', text) #get rid of by lines
        self.title = text
        
        return True
    
    def processText (self, text):
        text = re.sub(r'\([^)]*\)', ' ', text) # get rid of parentheticals (items within parens and parens)
        text = re.sub(r"[^a-zA-Z0-9/().]+", ' ', text) # get rid of special characters
        return text
        
    def processHeading (self, text):
        text = text.strip().lower()
        if "cupcakes" in text or "batter" in text or "cake" in text:
            return "main"
        if "filling" in text:
            return "filling"
        if "frosting" in text or "buttercream" in text or "glaze" in text or "icing" in text:
            return "frosting"
        if "crust" in text:
            return "crust"
        if "ganache" in text:
            return "ganache"
        if "topping" in text or "decoration" in text or "decorating" in text or "decorate" in text:
            return "topping"
        if "curd" in text:
            return "curd"
        if "syrup" in text:
            return "syrup"
        if "sauce" in text:
            return "sauce"
        text = re.sub(r"[^a-zA-Z0-9]+", ' ', text)
        
        remove_list = ['for', 'to', 'the', 'a', ]
        word_list = text.split()
        text = ' '.join([i for i in word_list if i not in remove_list])
        return text.strip().replace(" ", "_")
        
    def parseIngredients (self):
        list = self.soup.find_all("div", {"class" : "c-ingredientGroup"})
        if len(list) == 0:
            return False
            
        switcher = self.soup.find_all("div", {"class" : "c-metricSwitcher"})
        
        # if contains both metric and imperial version of ingredients
        # only take one set
        if len(switcher) > 0:
            list = list[:len(list)//2]
        
        
        ing = []
        
        for item in list:
            title = item.find("h3")
            if title == None:
                title = "main"
            else:
                title = self.processHeading(title.text)
            sub = item.find_all("li", {"class" : "c-ingredientGroup__item"})
            ing.append({title: [self.processText(item.text) for item in sub]})
            
        self.ingredients = ing
        return True
    
    
    def tokenize_sentences (self, array):
        text = " ".join(array)
        text = re.sub(r"[^a-zA-Z0-9/().]+", ' ', text) # get rid of special characters
        text = re.sub(r'\([^)]*\)', '', text) #get rid of parentheticals (items within parens and parens)
        text = re.sub(r'[^^](I ).*[.]', '', text) #get rid of asides (e.g., I recomend)
        text = re.sub(r'[^^](Watch my ).*[.]', '', text) #get rid of asides (e.g., I recomend)
        text = re.sub(r'[^^](Watch video ).*[.]', '', text) #get rid of asides (e.g., I recomend)
        steps = []
        list = nltk.tokenize.sent_tokenize(text)
        for sentence in list:
            steps.append(sentence)
        return steps
    
    
    def parseSteps (self):
        list = self.soup.select(".c-recipeMethod__cmsContent")
        if len(list) == 0:
            return False
        steps = [item.text for item in list]
        self.steps = self.tokenize_sentences(steps)
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
  query = "&query=pie"
  
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
    with open('pastry.csv', mode='a') as recipe_file:
        writer = csv.writer(recipe_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for index in range(len(self.links)):
            if self.parser.run(self.links[index]) == True:
                # get parsed object
                json = self.parser.getJSON()
                #write to csv
                writer.writerow([json["title"], json["yield"], json["ingredients"], json["steps"], json["url"]]) #
    recipe_file.close()
 
  def run (self):
    for page in range(2, 10):
        self.makeSoup(page)
    self.parseAndWriteLinks()
  
  


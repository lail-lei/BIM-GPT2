import re
import csv
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
import nltk
nltk.download('punkt')


class ProjectParser ():
    
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
        if self.soup.find("h2") == None:
            return False
        self.title = self.soup.find("h2", {"class": "wprm-recipe-name"}).text.strip()
        return True
    
    
    
    
    
    def processIngredientText(self, text):
        text = re.sub(r'\([^)]*\)', ' ', text) # get rid of parentheticals (items within parens and parens)
        text = re.sub(r"[^a-zA-Z0-9/().]+", ' ', text) # get rid of special characters
        return text.strip()
    
    def parseIngredients (self):
        # get all ingredients
        list = self.soup.select(".wprm-recipe-ingredient")
        # return false if no ingredients
        if len(list) == 0:
            return False
        self.ingredients = [{"text": self.processIngredientText(item.text)} for item in list]
        return True
        
    
    def processStepText (self, text):
        text = re.sub(r'\([^)]*\)', ' ', text) # get rid of parentheticals (items within parens and parens)
        text = re.sub(r'[^^](I ).*[.]', '', text) #get rid of asides (e.g., I recomend)
        text = re.sub(r'[^^](Watch my ).*[.]', '', text) #get rid of asides (e.g., I recomend)
        text = re.sub(r'[^^](Watch video ).*[.]', '', text) #get rid of asides (e.g., I recomend)
        text = re.sub(r"[^a-zA-Z0-9/().]+", ' ', text) # get rid of special characters
        return text.strip()
    
    def parseSteps (self):
        # get all steps
        list = self.soup.select(".wprm-recipe-instruction")
        # return false if no steps
        if len(list) == 0:
            return False
        # join steps into a string, and process to get rid of asides, parentheticals, and special characters
        text = " ".join(list)
        text = self.processStepText(text);
        # set global variable
        self.steps = nltk.tokenize.sent_tokenize(text)
        # return true
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
        # remove strong tags to keep instructions just instructions
        # separate steps based on sentences
        for item in list:
            if(item.find("strong")):
                item.find("strong").decompose()
            text = re.sub(r"[^a-zA-Z0-9.,()]+", ' ', item.text)
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
                
    def parse (self):
       
        serves = self.soup.find("span", {"class": "tasty-recipes-yield"})
        if serves:
            self.yields = serves.text
        else:
            self.yields = "12 cupcakes" #replace missing yield with common yield
        self.ingredients = self.parseIngredients(self.soup.select(".tasty-recipes-ingredients-body li"))
        self.steps = self.parseSteps(self.soup.select(".tasty-recipes-instructions-body li"))
        self.tags = self.parseTags(self.soup.find("article", {"class": "post"}))
        
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
        self.parse()



class ProjectSpider:

  # hosts all cupcake recipes on the site
  directory = "https://www.cupcakeproject.com/category/cupcakes/page/;
  
  links = [] # resulting list of links from scrape
  parser = ProjectParser()
  
  def _init_ (self):
    self.soup = None
    
  
  def makeSoup (self, page):
    # make request to disguise scraping
    url = self.directory + str(page) + "/";
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    self.soup = BeautifulSoup(webpage, "html.parser")
    
  def consumeSoup (self):
    library = self.soup.select('.title a', recursive=False)
    for element in library:
        self.links.append(element['href'])
      
  # keep copy of urls scraped
  def parseAndWriteLinks (self):
    with open('cupcakes_test.csv', mode='a') as recipe_file:
        writer = csv.writer(recipe_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for index in range(len(self.links)):
            # run parser on url
            self.parser.run(self.links[index])
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
  

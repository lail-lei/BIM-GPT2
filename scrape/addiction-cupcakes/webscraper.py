import re
import csv
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
import nltk
nltk.download('punkt')


class AddictionParser ():
    
    description = None
    
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
        
    

    def isolateTag (self, text):
        rep = {"category": "", "tag": "", "-": " "}
        rep = dict((re.escape(k), v) for k, v in rep.items())
        pattern = re.compile("|".join(rep.keys()))
        return pattern.sub(lambda m: rep[re.escape(m.group(0))], text).strip()

    def parseTags (self, html):
     
        prefixes=("category", "tag") # these are our tag classes
        list = html["class"]
        tags = [x for x in list if x.startswith(prefixes)]
        # now tags only has category- and tag- classes
        for index, tag in enumerate(tags):
            tags[index] = self.isolateTag(tag)

        return tags
      
    
    def parseTitle (self):
        title = self.soup.find("h1", {"class": "article-heading"})
        if title == None:
            return False
        self.title = title.text
        return True
        
    def parseYield (self):
        serves = self.soup.select(".mv-create-time-yield span")
        if serves:
            self.yields = serves[0].text
        else:
            self.yields = "12 cupcakes" #replace missing yield with common yield
        return True
    
    
    def parseIngredients (self):
        
        if self.soup.find("div", {"class" : "mv-create-ingredients"}) == None and self.soup.find("div", {"class" : "ingredients"}) == None:
                return False
        
        if self.soup.find("div", {"class" : "mv-create-ingredients"}) != None:
            list = self.soup.select(".mv-create-ingredients li")
            if len(list) == 0:
                list = self.soup.select(".mv-create-ingredients p")
                if len(list) == 0:
                    list = self.soup.select(".mv-create-ingrediets div")
                    
        elif self.soup.find("div", {"class" : "ingredients"}) != None:
            list = self.soup.select(".ingredients li")
            if len(list) == 0:
                list = self.soup.select(".ingredients li")
                if len(list) == 0:
                    list = self.soup.select(".ingredients p")
                    if len(list) == 0:
                        list = self.soup.select(".ingredients div")
            
        
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
            
        self.ingredients = ingredients
        
        return True
    
    def parseSteps (self):
        
        if self.soup.find("div", {"class" : "mv-create-instructions"}) == None and self.soup.find("div", {"class" : "instructions"}) == None:
                return False
                
                
        if self.soup.find("div", {"class" : "mv-create-instructions"}) != None:
            list = self.soup.select(".mv-create-instructions li")
            if len(list) == 0:
                list = self.soup.select(".mv-create-instructions p")
                if len(list) == 0:
                    list = self.soup.select(".mv-create-instructions div")
                    
        elif self.soup.find("div", {"class" : "instructions"}) != None:
            list = self.soup.select(".instructions li")
            if len(list) == 0:
                list = self.soup.select(".instructions li")
                if len(list) == 0:
                    list = self.soup.select(".instructions p")
                    if len(list) == 0:
                        list = self.soup.select(".instructions div")
        
        steps = []
        # remove strong tags to keep instructions just instructions
        # separate steps based on sentences
        for item in list:
            text = re.sub("^[0-9].|^\n|^\n1.", "", item.text) #remove step number
            text = re.sub(r"[^a-zA-Z0-9.,()]+", ' ',text)
            text = text.strip()
            list = nltk.tokenize.sent_tokenize(text)
            for sentence in list:
                steps.append(sentence)
        
        self.steps = steps
        return True
        
        
      
    def parse (self):
        
        if self.parseTitle() == False:
            return False
        
        if self.parseIngredients() == False:
            return False
            
        if self.parseSteps() == False:
            return False

        # non essential fields below
        self.parseYield() # fills in with most common
        
        self.tags = self.parseTags(self.soup.find("div", {"id" : re.compile('^post-')}))
        img = self.soup.find("img", {"class": "mv-create-image"})
        if img != None and img.has_attr("description"):
            self.description = img["description"]
            
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
        json["description"] = self.description
        return json
        
        
    def run (self, url):
        self.url = url
        self.makeSoup()
        return self.parse()



class AddictionSpider:

  # hosts all cupcake recipes on the site
  directory = "https://www.mybakingaddiction.com/page/"
  search = "/?s=cupcakes"
  
  links = [] # resulting list of links from scrape
  parser = AddictionParser()
  
  def _init_ (self):
    self.soup = None
    
  
  def makeSoup (self, page):
    # make request to disguise scraping
    url = self.directory + str(page) + self.search;
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    self.soup = BeautifulSoup(webpage, "html.parser")
    
  def consumeSoup (self):
    library = self.soup.select(".excerpt-photo a")
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
                writer.writerow([json["title"], json["yield"], json["ingredients"], json["steps"], json["url"], json["tags"]])
    recipe_file.close()
    
 
 
  def run (self):
    for page in range(10, 21):
        self.makeSoup(page)
        self.consumeSoup()
    self.parseAndWriteLinks()
  

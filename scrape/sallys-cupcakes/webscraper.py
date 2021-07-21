import re
import csv
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
import nltk
nltk.download('punkt')


class SallyParser ():
    ingredients = []
    def _init_ (self):
        self.title = ""
        self.tags = []
        self.steps = []
        self.serves = "12 cupcakes"
        self.soup = None
        self.url = None
   
    
    def makeSoup (self):
        # make request to disguise scraping
        req = Request(self.url, headers={'User-Agent': 'Mozilla/5.0'})
        webpage = urlopen(req).read()
        self.soup = BeautifulSoup(webpage, "html.parser")
        
    def parseTitle (self):
        title = self.soup.find("h1", {"class": "entry-title"})
        if title == None:
            return False
        text = title.text
        text = re.sub(r'\([^)]*\)', ' ', text) # get rid of parentheticals (items within parens and parens)
        text = re.sub(r"[^a-zA-Z0-9/().]+", ' ', text) # get rid of special characters
        self.title = text
        return True
        
    def parseYield (self):
        serves = self.soup.find("span", {"class": "tasty-recipes-yield"})
        if serves:
            self.serves = serves.text
        else:
            self.serves = "12" #replace missing yield with common yield
        
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
        if "topping" in text or "decoration" in text or "decorating" in text:
            return "topping"
        if "curd" in text:
            return "curd"
        if "syrup" in text:
            return "syrup"
        text = re.sub(r"[^a-zA-Z0-9]+", ' ', text)
        text = re.sub(r'(for the ).*[.]', '', text)
        return text.strip().replace(" ", "_")
        
    def parseHeadings (self):
        list = self.soup.select(".tasty-recipes-ingredients-body h4")
        if len(list) == 0:
            list = self.soup.select(".tasty-recipes-ingredients-body h3")
        headings = [self.processHeading(item.text) for item in list]
        return headings;
    
    def processIngredient (self, text):
         text = re.sub(r'\([^)]*\)', ' ', text) # get rid of parentheticals (items within parens and parens)
         text = re.sub(r"[^a-zA-Z0-9/().]+", ' ', text) # get rid of special characters
         return text;
        
    def parseIngredientList (self, uls):
        processed = []
        for ul in uls:
            items = [ self.processIngredient(li.text) for li in ul.findAll('li')]
            processed.append(items)
        return processed
        
    def parseIngredients (self):
        ingredients_list = self.soup.select(".tasty-recipes-ingredients-body ul")
        
        if len(ingredients_list) == 0:
            return False;
        
        body = self.parseIngredientList(ingredients_list)
     
        if len(body) <= 0:
            return False;
            
        if len(body) == 1:
            self.ingredients.append({"main" : body[0]})
            return True;
        
        # more than 1 subrecipe
        # get headings
        headings = self.parseHeadings();

        # equal number of headings to body
        if len(headings) == len(body):
            ingredients = []
            for i in range(len(body)):
                ingredients.append({headings[i]: body[i]})
            
            self.ingredients = ingredients
            return True
        
        if len(body) == len(headings) + 1:
            ingredients = []
            # first subgroup is typically batter
            ingredients.append({"main": body[0]})
            for i in range(1, len(headings)):
                ingredients.append({headings[i]: body[i]})
            
            self.ingredients = ingredients
            return True
        
        
        # hard to tell what's going on if more than 1 subrecipe and not 1 to 1 heading
        return False
            
    def tokenize_sentences (self, array):
        text = " ".join(array)
        text = re.sub(r"[^a-zA-Z0-9/().]+", ' ', text) # get rid of special characters
        text = re.sub(r'\([^)]*\)', '', text) #get rid of parentheticals (items within parens and parens)
        text = re.sub(r'[^^](I ).*[.]', '', text) #get rid of asides (e.g., I recomend)
        text = re.sub(r'[^^](Watch my ).*[.]', '', text) #get rid of asides (e.g., I recomend)
        text = re.sub(r'[^^](Watch video ).*[.]', '', text) #get rid of asides (e.g., I recomend)
        text = text.strip()
        steps = []
        list = nltk.tokenize.sent_tokenize(text)
        for sentence in list:
            steps.append(sentence)
        return steps
   
    def parseSteps (self):
        list = self.soup.select(".tasty-recipes-instructions-body li")
        if len(list)== 0:
            return False
        
        steps = [item.text for item in list]
        self.steps = self.tokenize_sentences(steps)
        
        return True
        

    def isolateTag (self, text):
        rep = {"category": "", "tag": "", "-": " "}
        rep = dict((re.escape(k), v) for k, v in rep.items())
        pattern = re.compile("|".join(rep.keys()))
        return pattern.sub(lambda m: rep[re.escape(m.group(0))], text)

    def parseTags (self):
        html = self.soup.find("article", {"class": "post"})
        prefixes=("category", "tag") # these are our tag classes
        list = html["class"]
        tags = [x for x in list if x.startswith(prefixes)]
        # now tags only has category- and tag- classes
        for index, tag in enumerate(tags):
            tags[index] = self.isolateTag(tag)
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
        json["yield"] = self.serves
        json["ingredients"] = self.ingredients
        json["steps"] = self.steps
        json["url"] = self.url
        json["tags"] = self.tags
        return json
        
        
    def run (self, url):
        self.url = url
        self.makeSoup()
        self.parse()



class SallySpider:

  # hosts all cupcake recipes on the site
 
  directory =  "https://sallysbakingaddiction.com/category/desserts/pies-crisps-tarts/page/"
  
  links = [] # resulting list of links from scrape
  parser = SallyParser()
  
  def _init_ (self):
    self.soup = None
    
  
  def makeSoup (self, page):
    # make request to disguise scraping
    url = self.directory + str(page) + "/"
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    self.soup = BeautifulSoup(webpage, "html.parser")
    
  def consumeSoup (self):
    library = self.soup.select('.c-archive-post a', recursive=False)
    for element in library:
        self.links.append(element['href'])
      
  # keep copy of urls scraped
  def parseAndWriteLinks (self):
    with open('pies.csv', mode='a') as recipe_file:
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
    for page in range(1, 7):
        self.makeSoup(page)
        self.consumeSoup()
    self.parseAndWriteLinks()
  

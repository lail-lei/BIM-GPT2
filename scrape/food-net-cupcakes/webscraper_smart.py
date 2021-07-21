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
        self.steps = []
        self.yields = None
        self.soup = None
        self.url = None
        self.ingredients = []
    
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
        

    def parse_multiple_sub_recipes (self, has_sub_recipe):
        try:
            ing = []
            titles = []
            obj = []
            
            for index in range(len(has_sub_recipe)):
                heading = has_sub_recipe[index]
                titles.append(self.processHeading(heading.text))
                children = heading.find_all_next("p", {"class": "o-Ingredients__a-Ingredient"})
                children = [self.processText(item.text) for item in children]
                ing.append(children);
            
            cut_back = len(ing[-1]) #get length of last subrecipe in list
                
            # starting at second to last position, count backwards
            for index in range(len(ing) - 2, -1, -1):
                current = ing[index]
                cut_from = len(current) - cut_back # index to remove items from
                current = current[:cut_from]
                ing[index] = current
                cut_back += len(current)
                
            for index in range(len(titles)):
                current = {titles[index]: ing[index]}
                obj.append(current)
            
            self.ingredients = obj
            return True
        except:
            return False
    
    def parse_single_sub_recipe (self, has_sub_recipe):
        try:
            heading = has_sub_recipe[0]
            title = self.processHeading(heading.text)
            obj = []
            sub = heading.find_all_next("p", {"class": "o-Ingredients__a-Ingredient"})
            sub = [self.processText(item.text) for item in sub]
            obj.append({title: sub})
            main = heading.find_all_previous("p")
            if len(main) > 0:
                main.pop(len(main)-1) # going backwards, remove recipe noise (deselect option)
                main = [self.processText(item.text) for item in main]
                obj.append({"main": main})
            self.ingredients = obj
            return True
        except:
            print("excepted")
            return False
                
            
    def parseIngredients (self):
        
        has_ingredients = self.soup.select(".o-Ingredients__a-Ingredient")
        if len(has_ingredients) == 0:
            return False
        has_sub_recipe = self.soup.select(".o-Ingredients__a-SubHeadline")
        # if frosting ingredients exist
        
        
        if len(has_sub_recipe) > 1:
            return self.parse_multiple_sub_recipes(has_sub_recipe)
        
        if len(has_sub_recipe) == 1:
            return self.parse_single_sub_recipe(has_sub_recipe)
        else:
            ingredients = [self.processText(item.text) for item in has_ingredients]
            ingredients.pop(0) # pop noise (deselect option)
            self.ingredients = [{"main": ingredients}]
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
        list = self.soup.select(".o-Method__m-Step")
        if len(list) == 0:
            return False
        steps = [item.text for item in list]
        self.steps = self.tokenize_sentences(steps)
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
#  directory = "https://www.foodnetwork.com/search/cupcakes-/p/";
#  query = "/CUSTOM_FACET:RECIPE_FACET"
    
  directory = "https://www.foodnetwork.com/search/cakes-/p/"
  query = "/DISH_DFACET:0/tag%23dish:cake"

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
    with open('cakes.csv', mode='a') as recipe_file:
        writer = csv.writer(recipe_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for index in range(len(self.links)):
            # run parser on url
            if self.parser.run(self.links[index]) == True:
                # get parsed object
                json = self.parser.getJSON()
                # write to csv
                writer.writerow([json["title"], json["yield"], json["ingredients"], json["steps"], json["url"], json["tags"]])
    recipe_file.close()
    
 
 # 60 cupcakes
 #179 cakes
  def run (self):
    for page in range(88, 180):
        self.makeSoup(page)
        self.consumeSoup()
    self.parseAndWriteLinks()
  


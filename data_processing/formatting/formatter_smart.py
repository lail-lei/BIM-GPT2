import re
import nltk
nltk.download('punkt')

class Formatter ():
    
    def _init_ (self):
        result = None
        raw = None
    
    
    def createInput (self):
        input = self.raw["keywords"]
        self.result += "<INPUT_START> "
        i = 0
        for i in range(len(input)-1):
            self.result += input[i]+ " <NEXT_INPUT> "
        self.result += input[i+1]+ " <INPUT_END> "
        
        
    def process_ingredient_type(self, ingredients, type):
        self.result +=  "<"+type+"_START> "
        for i in range(0, len(ingredients)):
            self.result +=  ingredients[i]
            if i == len(ingredients)-1:
                self.result += " <"+type+"_END> "
            else:
                self.result +=  " <NEXT_"+type+"> "
        
        
        
    def process_sub_group (self, group, type):
        self.result +=  "<"+type+"_INGREDIENTS_START> "
        if "premade" in group:
            self.process_ingredient_type(group["premade"], "PREMADE")
        if "prep" in group:
            self.process_ingredient_type(group["prep"], "PREP")
        if "fat" in group:
            self.process_ingredient_type(group["fat"], "FAT")
        if "structural" in group:
            self.process_ingredient_type(group["structural"], "STRUCTURAL")
        if "moistening" in group:
            self.process_ingredient_type(group["moistening"], "MOISTENING")
        if "sweetener" in group:
            self.process_ingredient_type(group["sweetener"], "SWEETENER")
        if "leavener" in group:
            self.process_ingredient_type(group["leavener"], "LEAVENER")
        if "flavoring" in group:
            self.process_ingredient_type(group["flavoring"], "FLAVORING")
        self.result +=  "<"+type+"_INGREDIENTS_END> "
        

    def processLabel(self, text):
        return re.sub(r"[^a-zA-Z]+", '', text).strip()
        
        
    def createIngredients (self):
        
        ingredients = self.raw["ingredients"]
        self.result += "<INGREDIENTS_START> "
        
        #group_names = [k for d in ingredients for k in d.keys()]
        # add by group
        for group in ingredients:
            key = list(group.keys())[0]
            self.process_sub_group(group[key], self.processLabel(key.upper()))
        self.result += "<INGREDIENTS_END> "
        
            
    def createSteps (self):
        steps = self.raw["steps"]
        self.result += "<STEP_START> "
        for i in range(0, len(steps)):
            self.result += steps[i]
            if i == len(steps)-1:
                self.result += " <STEP_END> "
            else:
                self.result += " <NEXT_STEP> "    
    
    def createTitle (self):
        self.result += "<TITLE_START> " + self.raw["title"] + " <TITLE_END> "
    
    def createYield (self):
        self.result += "<YIELD_START> " + self.raw["yield"] + " <YIELD_END> "
        
    
    def buildString (self):
        self.result = "<RECIPE_START> "
        self.createInput()
        self.createYield()
        self.createIngredients()
        self.createSteps()
        self.createTitle()
        self.result += "<RECIPE_END>"
    
    
    def run (self, object):
        self.raw = object
        self.buildString()
    
    def getString (self):
        return self.result
    


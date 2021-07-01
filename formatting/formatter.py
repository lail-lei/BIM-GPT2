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
        
    
    def createIngredients (self):
        ingredients = self.raw["ingredients"]
        self.result += "<INGREDIENT_START> "
        for i in range(0, len(ingredients)):
            self.result += ingredients[i]["text"]
            if i == len(ingredients)-1:
                self.result += " <INGREDIENT_END> "
            else:
                self.result += " <NEXT_INGREDIENT> "
            
    # forgot to tokenize steps by sentence when scraping foodnetwork, amy's cupcakes, and mad baking :(
    # so to remedy this, let's add a step to tokenize by sentence here.
    def tokenize_sentences (self, array):
        text = " ".join(array)
        text = re.sub(r'\([^)]*\)', '', text) #get rid of parentheticals (items within parens and parens)
        text = re.sub(r'[^^](I ).*[.]', '', text) #get rid of asides (e.g., I recomend)
        text = re.sub(r'[^^](Watch my ).*[.]', '', text) #get rid of asides (e.g., I recomend)
        text = re.sub(r'[^^](Watch video ).*[.]', '', text) #get rid of asides (e.g., I recomend)
        steps = []
        list = nltk.tokenize.sent_tokenize(text)
        for sentence in list:
            steps.append(sentence)
        return steps
    
    def createSteps (self):
        steps = self.tokenize_sentences(self.raw["steps"])
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
    



class Formatter ():
    
    def _init_ (self):
        result = None
        raw = None
    
    
    def createInput (self):
        input = self.raw["tags"]
        self.result += "<INPUT_START> "
        for i in range(len(input)-1):
            self.result += input[i]+ " <NEXT_INPUT> "
        self.result += input[i + 1] + " <INPUT_END> "
        
    
    def createIngredients (self):
        ingredients = self.raw["ingredients"]
        self.result += "<INGREDIENT_START> "
        for i in range(len(ingredients)-1):
            self.result += ingredients[i]["text"]+ " <NEXT_INGREDIENT> "
        self.result += ingredients[i + 1]["text"] + " <INGREDIENT_END> "
    
    def createSteps (self):
        steps = self.raw["steps"]
        self.result += "<STEP_START> "
        for i in range(len(steps)-1):
            self.result += steps[i]+ " <NEXT_STEP> "
        self.result += steps[i + 1] + " <STEP_END> "
    
    
    def createTitle (self):
        self.result += "<TITLE_START> " + self.raw["title"] + " <TITLE_END> "
    
    def createYield (self):
        self.result += "<YIELD_START> " + self.raw["yield"] + " <YIELD_END> "
    
    def buildString (self):
        self.result = "<RECIPE_START> "
        self.createInput()
        self.createIngredients()
        self.createSteps()
        self.createTitle()
        self.result += "<RECIPE_END>"
    
    
    def run (self, object):
        self.raw = object
        self.buildString()
    
    def getString (self):
        return self.result
    


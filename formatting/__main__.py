from csv import reader
from pathlib import Path
from formatter import Formatter
import ast # for json string of list of dicts to list of dicts


# for formatting
fm = Formatter()

# read in csv, create objects, and save to list
objects = []
path = Path(__file__).parent / "../cupcakes.csv"
with path.open() as csvf:
    csv_reader = reader(csvf)
    for row in csv_reader:
        obj = {}
        obj["title"] = row[0]
        obj["yield"] = row[1]
        obj["ingredients"] = ast.literal_eval(row[2])
        obj["steps"] = ast.literal_eval(row[3])
        obj["tags"] = ast.literal_eval(row[5])
        fm.run(obj) # format
        objects.append(fm.getString()) #and append formatted obj
csvf.close()

with open('formatted_recipes.txt', mode='w') as recipe_file:
    for recipe in objects:
        # write formatted to file
        recipe_file.write(recipe)
recipe_file.close()

from csv import reader
from pathlib import Path
from formatter_smart import Formatter
from collections import defaultdict
import ast # for json string of list of dicts to list of dicts



def arrange_into_sub_groups (ingredients):
    ing_list = []
    for key in ingredients:
        object = defaultdict(list)
        for ing in ingredients[key][0]:
            object[ing["type"]].append(ing["ingredient"])
        ing_list.append({key: dict(object)})
    return ing_list
           



# for formatting
fm = Formatter()

# read in csv, create objects, and save to list
objects = []
path = Path(__file__).parent / "../cupcakes_with_frosting_processed_keywords.csv"
with path.open() as csvf:
    csv_reader = reader(csvf)
    for row in csv_reader:
        obj = {}
        obj["title"] = row[0]
        obj["yield"] = row[1]
        obj["ingredients"] = arrange_into_sub_groups(ast.literal_eval(row[8]))
        obj["steps"] = ast.literal_eval(row[3])
        obj["keywords"] = ast.literal_eval(row[7])
        fm.run(obj) # format
        objects.append(fm.getString()) #and append formatted obj
csvf.close()




with open('formatted_recipes_with_processed_ingredients1.txt', mode='w') as recipe_file:
    for recipe in objects:
        # write formatted to file
        recipe_file.write(recipe)
recipe_file.close()

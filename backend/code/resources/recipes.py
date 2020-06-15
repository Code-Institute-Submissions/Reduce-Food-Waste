from flask_restful import Resource, reqparse
from flask import request

from models import mongo, ValidationError
from models.recipes import RecipesModel
from pymongo.collection import ObjectId

class Recipe(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('name',
                        type=str,
                        required=True,
                        help="Recipe must have a name")
    parser.add_argument('description',
                        type=str,
                        required=True,
                        help="Recipe must have a description")
    parser.add_argument('image',
                        type=str,
                        required=True,
                        help="Recipe must have a image")
    parser.add_argument('method',
                        action='append',
                        required=True,
                        help="Recipe must have a method")
    parser.add_argument('ingredients',
                        action='append',
                        required=True,
                        help="Recipe must have ingredients")

    def get(self, recipe_id):
        recipe = RecipesModel.find_by_id(recipe_id)

        if recipe is None:
             return {"message": "A recipe with that ID does not exist"}, 404

        return RecipesModel.return_as_object(recipe)


    def put(self, recipe_id):
        request_data = request.json

        if not RecipesModel.find_by_id(recipe_id):
            return {"message": "A Recipe with that ID does not exist"}


        try:
            updated_recipe = RecipesModel.build_recipe_from_request(request_data)
            mongo.db.recipes.update({"_id": ObjectId(recipe_id)}, updated_recipe)
            updated_recipe['_id'] = recipe_id
            return RecipesModel.return_as_object(updated_recipe)

        except ValidationError as error:
            return {"message": error.message}, 400
        except:
            return {"message": "An error occurred saving to database"}, 500


    def delete(self, recipe_id):
        recipe = RecipesModel.find_by_id(recipe_id)

        if not recipe:
            return {"message": "A recipe with this name does not exist"}

        mongo.db.recipes.remove({"_id": ObjectId(recipe_id)})

        return {"message": "Recipe deleted"}, 200




class RecipeCollection(Resource):
    def get(self):
        recipes = [
            RecipesModel.return_as_object(recipe)
            for recipe in mongo.db.recipes.find()
        ]

        return {
            'recipes': recipes
        }

    def post(self):
        request_data = request.json

        if RecipesModel.find_by_name(request_data['name']):
           return {'message': "A recipe with name '{}' already exists".format(request_data['name'])}, 400

        try:
            request_data = RecipesModel.build_recipe_from_request(request_data)
            result = mongo.db.recipes.insert_one(request_data)
            request_data['_id'] = result.inserted_id

            return RecipesModel.return_as_object(request_data)

        except ValidationError as error:
            return {"message": error.message}, 400
        except:
            return {"message": "An error occurred"}, 500

class RecipeSearch(Resource):
    def post(self):
        request_data = request.json

        myquery = {}

        for allergy in request_data.get('allergens', []):
            myquery["allergies." + allergy] = True

        ingredient_list = []

        for ingredient_id in request_data.get('ingredient_ids', []):
            ingredient_list.append({"$elemMatch": {"ingredient._id": ingredient_id}})

        myquery["ingredients"] = {"$all" : ingredient_list}

        recipes = [
            RecipesModel.return_as_object(recipe)
            for recipe in mongo.db.recipes.find(myquery)
        ]

        return {
            'recipes': recipes
        }



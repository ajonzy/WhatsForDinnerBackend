from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://" + os.environ.get("DATABASE_URL").partition("://")[2]

db = SQLAlchemy(app)
ma = Marshmallow(app)
CORS(app)

# SQLAlchemy Tables
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False, unique=False)
    email = db.Column(db.String, nullable=False, unique=False)
    meals = db.relationship("Meal", backref="user", cascade='all, delete, delete-orphan')
    
    def __init__(self, username, password, email):
        self.username = username
        self.password = password
        self.email = email

class Meal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=False)
    description = db.Column(db.String, nullable=True, unique=False)
    image_url = db.Column(db.String, nullable=True, unique=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    recipe = db.relationship("Recipe", backref="meal", cascade='all, delete, delete-orphan')
    
    def __init__(self, name, description, image_url, user_id):
        self.name = name
        self.description = description
        self.image_url = image_url
        self.user_id = user_id

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    meal_id = db.Column(db.Integer, db.ForeignKey("meal.id"), nullable=False)
    steps = db.relationship("Step", backref="recipe", cascade='all, delete, delete-orphan')
    ingredients = db.relationship("Ingredient", backref="recipe", cascade='all, delete, delete-orphan')
    
    def __init__(self, meal_id):
        self.meal_id = meal_id

class Step(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, nullable=False, unique=False)
    text = db.Column(db.String, nullable=False, unique=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipe.id"), nullable=False)
    
    def __init__(self, number, text, recipe_id):
        self.number = number
        self.text = text
        self.recipe_id = recipe_id

class Ingredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=False)
    amount = db.Column(db.String, nullable=False, unique=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipe.id"), nullable=False)
    
    def __init__(self, name, amount, recipe_id):
        self.name = name
        self.amount = amount
        self.recipe_id = recipe_id

# Marshmallow Schemas
class IngredientSchema(ma.Schema):
    class Meta:
        fields = ("id", "name", "amount", "recipe_id")

ingredient_schema = IngredientSchema()
multiple_ingredient_schema = IngredientSchema(many=True)

class StepSchema(ma.Schema):
    class Meta:
        fields = ("id", "number", "text", "recipe_id")

step_schema = StepSchema()
multiple_step_schema = StepSchema(many=True)

class RecipeSchema(ma.Schema):
    class Meta:
        fields = ("id", "steps", "ingredients")
    steps = ma.Nested(multiple_step_schema)
    ingredients = ma.Nested(multiple_ingredient_schema)

recipe_schema = RecipeSchema()
multiple_recipe_schema = RecipeSchema(many=True)

class MealSchema(ma.Schema):
    class Meta:
        fields = ("id", "name", "description", "image_url", "user_id", "recipe")
    recipe = base_fields.Function(lambda fields: recipe_schema.dump(fields.recipe[0]))

meal_schema = MealSchema()
multiple_meal_schema = MealSchema(many=True)

class UserSchema(ma.Schema):
    class Meta:
        fields = ("id", "username", "password", "email", "meals") # TODO Remove sensitive data
    meals = ma.Nested(multiple_meal_schema)

user_schema = UserSchema()
multiple_user_schema = UserSchema(many=True)

# Flask Endpoints


if __name__ == "__main__":
    app.run(debug=True)
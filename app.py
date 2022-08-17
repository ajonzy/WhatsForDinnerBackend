from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow, base_fields
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://" + os.environ.get("DATABASE_URL").partition("://")[2]

db = SQLAlchemy(app)
ma = Marshmallow(app)
bcrypt = Bcrypt(app)
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
    recipe = base_fields.Function(lambda fields: recipe_schema.dump(fields.recipe[0] if len(fields.recipe) > 0 else None))

meal_schema = MealSchema()
multiple_meal_schema = MealSchema(many=True)

class UserSchema(ma.Schema):
    class Meta:
        fields = ("id", "username", "password", "email", "meals") # TODO Remove sensitive data
    meals = ma.Nested(multiple_meal_schema)

user_schema = UserSchema()
multiple_user_schema = UserSchema(many=True)

# Flask Endpoints
@app.route("/user/add", methods=["POST"])
def add_user():
    if request.content_type != "application/json":
        return jsonify({
            "status": 400,
            "message": "Error: Data must be sent as JSON.",
            "data": {}
        })

    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    email = data.get("email")

    username_taken_check = db.session.query(User).filter(User.username == username).first()
    if username_taken_check is not None:
        return jsonify({
            "status": 400,
            "message": "Username already taken.",
            "data": {}
        })

    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

    record = User(username, hashed_password, email)
    db.session.add(record)
    db.session.commit()

    return jsonify({
        "status": 200,
        "message": "User Added",
        "data": user_schema.dump(record)
    })

@app.route("/user/get", methods=["GET"])
def get_all_users():
    records = db.session.query(User).all()
    return jsonify(multiple_user_schema.dump(records))

@app.route("/user/get/<id>", methods=["GET"])
def get_user_by_id(id):
    record = db.session.query(User).filter(User.id == id).first()
    return jsonify(user_schema.dump(record))

@app.route("/user/update/<id>", methods=["PUT"])
def update_user(id):
    if request.content_type != "application/json":
        return jsonify({
            "status": 400,
            "message": "Error: Data must be sent as JSON.",
            "data": {}
        })

    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    email = data.get("email")

    record = db.session.query(User).filter(User.id == id).first()
    if username is not None:
        username_taken_check = db.session.query(User).filter(User.username == username).first()
        if username_taken_check is not None:
            return jsonify({
                "status": 400,
                "message": "Username already taken.",
                "data": {}
            })
        record.username = username
    if password is not None:
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        record.password = hashed_password
    if email is not None:
        record.email = email

    db.session.commit()

    return jsonify({
        "status": 200,
        "message": "User Updated",
        "data": user_schema.dump(record)
    })

@app.route("/user/delete/<id>", methods=["DELETE"])
def delete_user(id):
    record = db.session.query(User).filter(User.id == id).first()
    db.session.delete(record)
    db.session.commit()
    return jsonify({
        "status": 200,
        "message": "User Deleted",
        "data": user_schema.dump(record)
    })

@app.route("/user/login", methods=["POST"])
def login_user():
    if request.content_type != "application/json":
        return jsonify({
            "status": 400,
            "message": "Error: Data must be sent as JSON.",
            "data": {}
        })

    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    record = db.session.query(User).filter(User.username == username).first()
    if record is None:
        return jsonify({
            "status": 400,
            "message": "Invalid username or password",
            "data": {}
        })

    password_check = bcrypt.check_password_hash(record.password, password)
    if password_check is False:
        return jsonify({
            "status": 400,
            "message": "Invalid username or password",
            "data": {}
        })

    return jsonify({
        "status": 200,
        "message": "Valid username and password",
        "data": user_schema.dump(record)
    })


@app.route("/meal/add", methods=["POST"])
def add_meal():
    if request.content_type != "application/json":
        return jsonify({
            "status": 400,
            "message": "Error: Data must be sent as JSON.",
            "data": {}
        })

    data = request.get_json()
    name = data.get("name")
    description = data.get("description")
    image_url = data.get("image_url")
    user_id = data.get("user_id")

    record = Meal(name, description, image_url, user_id)
    db.session.add(record)
    db.session.commit()

    return jsonify({
        "status": 200,
        "message": "Meal Added",
        "data": meal_schema.dump(record)
    })

@app.route("/meal/get", methods=["GET"])
def get_all_meals():
    records = db.session.query(Meal).all()
    return jsonify(multiple_meal_schema.dump(records))

@app.route("/meal/get/<id>", methods=["GET"])
def get_meal_by_id(id):
    record = db.session.query(Meal).filter(Meal.id == id).first()
    return jsonify(meal_schema.dump(record))

@app.route("/meal/update/<id>", methods=["PUT"])
def update_meal(id):
    if request.content_type != "application/json":
        return jsonify({
            "status": 400,
            "message": "Error: Data must be sent as JSON.",
            "data": {}
        })

    data = request.get_json()
    name = data.get("name")
    description = data.get("description")
    image_url = data.get("image_url")

    record = db.session.query(Meal).filter(Meal.id == id).first()
    if name is not None:
        record.name = name
    if description is not None:
        record.description = description
    if image_url is not None:
        record.image_url = image_url

    db.session.commit()

    return jsonify({
        "status": 200,
        "message": "Meal Updated",
        "data": meal_schema.dump(record)
    })

@app.route("/meal/delete/<id>", methods=["DELETE"])
def delete_meal(id):
    record = db.session.query(Meal).filter(Meal.id == id).first()
    db.session.delete(record)
    db.session.commit()
    return jsonify({
        "status": 200,
        "message": "Meal Deleted",
        "data": meal_schema.dump(record)
    })

if __name__ == "__main__":
    app.run(debug=True)
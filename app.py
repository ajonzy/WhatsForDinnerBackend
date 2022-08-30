from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow, base_fields
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv

import os
import random
import string

load_dotenv()

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://" + os.environ.get("DATABASE_URL").partition("://")[2]
app.wsgi_app = ProxyFix(app.wsgi_app)

db = SQLAlchemy(app)
ma = Marshmallow(app)
bcrypt = Bcrypt(app)
CORS(app)

# SQLAlchemy Tables
categories_table = db.Table('categories_table',
    db.Column('meal_id', db.Integer, db.ForeignKey('meal.id')),
    db.Column('category_id', db.Integer, db.ForeignKey('category.id'))
)

mealplans_table = db.Table('mealplans_table',
    db.Column('mealplan_id', db.Integer, db.ForeignKey('mealplan.id')),
    db.Column('meal_id', db.Integer, db.ForeignKey('meal.id'))
)

shared_meals_table = db.Table('shared_meals_table',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('meal_id', db.Integer, db.ForeignKey('meal.id'))
)

shared_mealplans_table = db.Table('shared_mealplans_table',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('mealplan_id', db.Integer, db.ForeignKey('mealplan.id'))
)

shared_shoppinglists_table = db.Table('shared_shoppinglists_table',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('shoppinglist_id', db.Integer, db.ForeignKey('shoppinglist.id'))
)

outgoing_friend_requests_table = db.Table('outgoing_friend_requests_table',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('friend_id', db.Integer, db.ForeignKey('user.id'))
)

incoming_friend_requests_table = db.Table('incoming_friend_requests_table',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('friend_id', db.Integer, db.ForeignKey('user.id'))
)

friends_table = db.Table('friends_table',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('friend_id', db.Integer, db.ForeignKey('user.id'))
)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False, unique=False)
    email = db.Column(db.String, nullable=False, unique=False)
    sessions = db.relationship("Session", backref="user", cascade='all, delete, delete-orphan')
    meals = db.relationship("Meal", backref="user", cascade='all, delete, delete-orphan')
    categories = db.relationship("Category", backref="user", cascade='all, delete, delete-orphan')
    mealplans = db.relationship("Mealplan", backref="user", cascade='all, delete, delete-orphan')
    shoppinglists = db.relationship("Shoppinglist", backref="user", cascade='all, delete, delete-orphan')
    shared_meals = db.relationship("Meal", secondary="shared_meals_table")
    shared_mealplans = db.relationship("Mealplan", secondary="shared_mealplans_table")
    shared_shoppinglists = db.relationship("Shoppinglist", secondary="shared_shoppinglists_table")
    outgoing_friend_requests = db.relationship("User", secondary="outgoing_friend_requests_table", primaryjoin=id==outgoing_friend_requests_table.c.user_id, secondaryjoin=id==outgoing_friend_requests_table.c.friend_id)
    incoming_friend_requests = db.relationship("User", secondary="incoming_friend_requests_table", primaryjoin=id==incoming_friend_requests_table.c.user_id, secondaryjoin=id==incoming_friend_requests_table.c.friend_id)
    friends = db.relationship("User", secondary="friends_table", primaryjoin=id==friends_table.c.user_id, secondaryjoin=id==friends_table.c.friend_id)
    
    def __init__(self, username, password, email):
        self.username = username
        self.password = password
        self.email = email

class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String, nullable=False, unique=True)
    ip = db.Column(db.String, nullable=False, unique=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    
    def __init__(self, token, ip, user_id):
        self.token = token
        self.ip = ip
        self.user_id = user_id

class Meal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=False)
    description = db.Column(db.String, nullable=True, unique=False)
    image_url = db.Column(db.String, nullable=True, unique=False)
    difficulty = db.Column(db.Integer, nullable=False, unique=False)
    sleep_until = db.Column(db.String, nullable=True, unique=False)
    user_username = db.Column(db.String, nullable=False, unique=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    recipe = db.relationship("Recipe", backref="meal", cascade='all, delete, delete-orphan')
    categories = db.relationship("Category", secondary="categories_table")
    mealplans = db.relationship("Mealplan", secondary="mealplans_table")
    shared_users = db.relationship("User", secondary="shared_meals_table")
    
    def __init__(self, name, description, image_url, difficulty, user_username, user_id):
        self.name = name
        self.description = description
        self.image_url = image_url
        self.difficulty = difficulty
        self.sleep_until = None
        self.user_username = user_username
        self.user_id = user_id

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    meals = db.relationship("Meal", secondary="categories_table")
    
    def __init__(self, name, user_id):
        self.name = name
        self.user_id = user_id

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    meal_id = db.Column(db.Integer, db.ForeignKey("meal.id"), nullable=False)
    stepsections = db.relationship("Stepsection", backref="recipe", cascade='all, delete, delete-orphan')
    steps = db.relationship("Step", backref="recipe", cascade='all, delete, delete-orphan')
    ingredients = db.relationship("Ingredient", backref="recipe", cascade='all, delete, delete-orphan')
    
    def __init__(self, meal_id):
        self.meal_id = meal_id

class Stepsection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False, unique=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipe.id"), nullable=False)
    steps = db.relationship("Step", backref="stepsection", cascade='all, delete, delete-orphan')
    
    def __init__(self, title, recipe_id):
        self.title = title
        self.recipe_id = recipe_id

class Step(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, nullable=False, unique=False)
    text = db.Column(db.String, nullable=False, unique=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipe.id"), nullable=False)
    stepsection_id = db.Column(db.Integer, db.ForeignKey("stepsection.id"), nullable=True)
    
    def __init__(self, number, text, recipe_id, stepsection_id):
        self.number = number
        self.text = text
        self.recipe_id = recipe_id
        self.stepsection_id = stepsection_id

class Ingredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=False)
    amount = db.Column(db.String, nullable=False, unique=False)
    category = db.Column(db.String, nullable=True, unique=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipe.id"), nullable=False)
    shoppingingredients = db.relationship("Shoppingingredient", backref="ingredient", cascade='all, delete, delete-orphan')
    
    def __init__(self, name, amount, category, recipe_id):
        self.name = name
        self.amount = amount
        self.category = category
        self.recipe_id = recipe_id

class Mealplan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=False)
    created_on = db.Column(db.String, nullable=False, unique=False)
    user_username = db.Column(db.String, nullable=False, unique=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    meals = db.relationship("Meal", secondary="mealplans_table")
    shoppinglist = db.relationship("Shoppinglist", backref="mealplan", cascade='all, delete, delete-orphan')
    shared_users = db.relationship("User", secondary="shared_mealplans_table")
    
    def __init__(self, name, created_on, user_username, user_id):
        self.name = name
        self.created_on = created_on
        self.user_username = user_username
        self.user_id = user_id

class Shoppinglist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=False)
    created_on = db.Column(db.String, nullable=False, unique=False)
    updates_hidden = db.Column(db.Boolean, nullable=False, unique=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    mealplan_id = db.Column(db.Integer, db.ForeignKey("mealplan.id"), nullable=True)
    shoppingingredients = db.relationship("Shoppingingredient", backref="shoppinglist", cascade='all, delete, delete-orphan')
    shared_users = db.relationship("User", secondary="shared_shoppinglists_table")
    
    def __init__(self, name, created_on, updates_hidden, user_id, mealplan_id):
        self.name = name
        self.created_on = created_on
        self.updates_hidden = updates_hidden
        self.user_id = user_id
        self.mealplan_id = mealplan_id

class Shoppingingredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=False)
    amount = db.Column(db.String, nullable=False, unique=False)
    category = db.Column(db.String, nullable=True, unique=False)
    obtained = db.Column(db.Boolean, nullable=False, unique=False)
    meal_name = db.Column(db.String, nullable=True, unique=False)
    shoppinglist_id = db.Column(db.Integer, db.ForeignKey("shoppinglist.id"), nullable=False)
    ingredient_id = db.Column(db.Integer, db.ForeignKey("ingredient.id"), nullable=True)
    
    def __init__(self, name, amount, category, meal_name, shoppinglist_id, ingredient_id):
        self.name = name
        self.amount = amount
        self.category = category
        self.obtained = False
        self.meal_name = meal_name
        self.shoppinglist_id = shoppinglist_id
        self.ingredient_id = ingredient_id

# Marshmallow Schemas
class ShoppingingredientSchema(ma.Schema):
    class Meta:
        fields = ("id", "name", "amount", "category", "obtained", "meal_name", "shoppinglist_id", "ingredient_id")

shoppingingredient_schema = ShoppingingredientSchema()
multiple_shoppingingredient_schema = ShoppingingredientSchema(many=True)

class ShoppinglistSchema(ma.Schema):
    class Meta:
        fields = ("id", "name", "created_on", "updates_hidden", "user_id", "mealplan_id", "shoppingingredients")
    shoppingingredients = ma.Nested(multiple_shoppingingredient_schema)

shoppinglist_schema = ShoppinglistSchema()
multiple_shoppinglist_schema = ShoppinglistSchema(many=True)

class IngredientSchema(ma.Schema):
    class Meta:
        fields = ("id", "name", "amount", "category", "recipe_id", "shoppingingredients")
    shoppingingredients = ma.Nested(multiple_shoppingingredient_schema)

ingredient_schema = IngredientSchema()
multiple_ingredient_schema = IngredientSchema(many=True)

class StepSchema(ma.Schema):
    class Meta:
        fields = ("id", "number", "text", "recipe_id", "stepsection_id")

step_schema = StepSchema()
multiple_step_schema = StepSchema(many=True)

class StepsectionSchema(ma.Schema):
    class Meta:
        fields = ("id", "title", "recipe_id", "steps")
    steps = ma.Nested(multiple_step_schema)

stepsection_schema = StepsectionSchema()
multiple_stepsection_schema = StepsectionSchema(many=True)

class RecipeSchema(ma.Schema):
    class Meta:
        fields = ("id", "meal_id", "stepsections", "steps", "ingredients")
    stepsections = ma.Nested(multiple_stepsection_schema)
    steps = ma.Nested(multiple_step_schema)
    ingredients = ma.Nested(multiple_ingredient_schema)

recipe_schema = RecipeSchema()
multiple_recipe_schema = RecipeSchema(many=True)

class CategorySchema(ma.Schema):
    class Meta:
        fields = ("id", "name", "user_id")

category_schema = CategorySchema()
multiple_category_schema = CategorySchema(many=True)

class MealSchema(ma.Schema):
    class Meta:
        fields = ("id", "name", "description", "image_url", "difficulty", "sleep_until", "categories", "user_username", "user_id", "recipe")
    categories = ma.Nested(multiple_category_schema)
    recipe = base_fields.Function(lambda fields: recipe_schema.dump(fields.recipe[0] if len(fields.recipe) > 0 else None))

meal_schema = MealSchema()
multiple_meal_schema = MealSchema(many=True)

class MealplanSchema(ma.Schema):
    class Meta:
        fields = ("id", "name", "created_on", "meals", "user_username", "user_id", "shoppinglist")
    meals = ma.Nested(multiple_meal_schema)
    shoppinglist = base_fields.Function(lambda fields: shoppinglist_schema.dump(fields.shoppinglist[0] if len(fields.shoppinglist) > 0 else None))

mealplan_schema = MealplanSchema()
multiple_mealplan_schema = MealplanSchema(many=True)

class UserSchema(ma.Schema):
    class Meta:
        fields = ("id", "username", "email", "meals", "categories", "mealplans", "shoppinglists", "shared_meals", "shared_mealplans", "shared_shoppinglists", "outgoing_friend_requests", "incoming_friend_requests", "friends")
    meals = ma.Nested(multiple_meal_schema)
    categories = ma.Nested(multiple_category_schema)
    mealplans = ma.Nested(multiple_mealplan_schema)
    shoppinglists = ma.Nested(multiple_shoppinglist_schema)
    shared_meals = ma.Nested(multiple_meal_schema)
    shared_mealplans = ma.Nested(multiple_mealplan_schema)
    shared_shoppinglists = ma.Nested(multiple_shoppinglist_schema)
    outgoing_friend_requests = base_fields.Function(lambda fields: list(map(lambda friend: { "user_id": friend.id, "username": friend.username }, fields.outgoing_friend_requests)))
    incoming_friend_requests = base_fields.Function(lambda fields: list(map(lambda friend: { "user_id": friend.id, "username": friend.username }, fields.incoming_friend_requests)))
    friends = base_fields.Function(lambda fields: list(map(lambda friend: { "user_id": friend.id, "username": friend.username }, fields.friends)))

user_schema = UserSchema()
multiple_user_schema = UserSchema(many=True)

# Flask Endpoints
# TODO Remove sensitive enpoints: get_user_by_id and delete_user(change to secure token)
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

    token = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(16))
    while db.session.query(Session).filter(Session.token == token).first() != None:
        token = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(16))

    hashed_ip = bcrypt.generate_password_hash(request.remote_addr).decode("utf-8")

    session = Session(token, hashed_ip, record.id)
    db.session.add(session)
    db.session.commit()

    return jsonify({
        "status": 200,
        "message": "User Added",
        "data": {
            "user": user_schema.dump(record),
            "token": token
        }
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

    token = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(16))
    while db.session.query(Session).filter(Session.token == token).first() != None:
        token = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(16))

    hashed_ip = bcrypt.generate_password_hash(request.remote_addr).decode("utf-8")

    session = Session(token, hashed_ip, record.id)
    db.session.add(session)
    db.session.commit()

    return jsonify({
        "status": 200,
        "message": "Valid username and password",
        "data": {
            "user": user_schema.dump(record),
            "token": token
        }
    })

@app.route("/user/friend/request", methods=["POST"])
def request_friend():
    if request.content_type != "application/json":
        return jsonify({
            "status": 400,
            "message": "Error: Data must be sent as JSON.",
            "data": {}
        })

    data = request.get_json()
    user_id = data.get("user_id")
    friend_username = data.get("friend_username")

    user = db.session.query(User).filter(User.id == user_id).first()
    friend = db.session.query(User).filter(User.username == friend_username).first()

    if friend is None:
        return jsonify({
            "status": 400,
            "message": "User doesn't exist.",
            "data": {}
        })
    if user.friends.count(friend) > 0:
        return jsonify({
            "status": 400,
            "message": "User already friended.",
            "data": {}
        })
    if user.outgoing_friend_requests.count(friend) > 0:
        return jsonify({
            "status": 400,
            "message": "Friend request already sent.",
            "data": {}
        })

    user.outgoing_friend_requests.append(friend)
    db.session.commit()

    friend.incoming_friend_requests.append(user)
    db.session.commit()

    return jsonify({
        "status": 200,
        "message": "Friend Request Added",
        "data": {
            "user": user_schema.dump(user),
            "friend": user_schema.dump(friend)
        }
    })

@app.route("/user/get", methods=["GET"])
def get_all_users():
    records = db.session.query(User).all()
    return jsonify(multiple_user_schema.dump(records))

@app.route("/user/get/id/<id>", methods=["GET"])
def get_user_by_id(id):
    record = db.session.query(User).filter(User.id == id).first()
    return jsonify(user_schema.dump(record))

@app.route("/user/get/token/<token>", methods=["GET"])
def get_user_by_token(token):
    session = db.session.query(Session).filter(Session.token == token).first()
    if session is None:
        return jsonify({
            "status": 403,
            "message": "User not authenticated.",
            "data": {}
        })
    if bcrypt.check_password_hash(session.ip, request.remote_addr) is False:
        return jsonify({
            "status": 403,
            "message": "User not authenticated.",
            "data": {}
        })

    record = db.session.query(User).filter(User.id == session.user_id).first()
    return jsonify({
        "status": 200,
        "message": "User authenticated.",
        "data": user_schema.dump(record)
    })

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
    for friend in record.friends:
        friend.friends.remove(record)
        db.session.commit()
        friend.incoming_friend_requests.remove(record)
        db.session.commit()
    db.session.delete(record)
    db.session.commit()
    return jsonify({
        "status": 200,
        "message": "User Deleted",
        "data": user_schema.dump(record)
    })

@app.route("/user/logout/single/<token>", methods=["DELETE"])
def logout_user(token):
    record = db.session.query(Session).filter(Session.token == token).first()
    db.session.delete(record)
    db.session.commit()
    return jsonify({
        "status": 200,
        "message": "User Logged Out",
        "data": {}
    })

@app.route("/user/logout/all/<id>", methods=["DELETE"])
def logout_user_all(id):
    record = db.session.query(User).filter(User.id == id).first()
    for session in record.sessions:
        db.session.delete(session)
        db.session.commit()
    return jsonify({
        "status": 200,
        "message": "User Logged Out",
        "data": {}
    })

@app.route("/user/friend/cancel/<id>/<friend_id>", methods=["DELETE"])
def cancel_friend_request(id, friend_id):
    user = db.session.query(User).filter(User.id == id).first()
    friend = db.session.query(User).filter(User.id == friend_id).first()
    
    if user.outgoing_friend_requests.count(friend) == 0:
        return jsonify({
                "status": 400,
                "message": "Error: Friend request does not exist.",
                "data": {}
            })

    user.outgoing_friend_requests.remove(friend)
    db.session.commit()

    friend.incoming_friend_requests.remove(user)
    db.session.commit()

    return jsonify({
        "status": 200,
        "message": "Friend Request Deleted",
        "data": {
            "user": user_schema.dump(user),
            "friend": user_schema.dump(friend)
        }
    })

@app.route("/user/friend/accept/<id>/<friend_id>", methods=["DELETE"])
def accept_friend_request(id, friend_id):
    user = db.session.query(User).filter(User.id == id).first()
    friend = db.session.query(User).filter(User.id == friend_id).first()
    
    if user.incoming_friend_requests.count(friend) == 0:
        return jsonify({
                "status": 400,
                "message": "Error: Friend request does not exist.",
                "data": {}
            })

    user.friends.append(friend)
    db.session.commit()

    friend.friends.append(user)
    db.session.commit()

    user.incoming_friend_requests.remove(friend)
    db.session.commit()

    friend.outgoing_friend_requests.remove(user)
    db.session.commit()

    if user.outgoing_friend_requests.count(friend) > 0:
        user.outgoing_friend_requests.remove(friend)
        db.session.commit()
        friend.incoming_friend_requests.remove(user)
        db.session.commit()

    return jsonify({
        "status": 200,
        "message": "Friend Added",
        "data": {
            "user": user_schema.dump(user),
            "friend": user_schema.dump(friend)
        }
    })

@app.route("/user/friend/reject/<id>/<friend_id>", methods=["DELETE"])
def reject_friend_request(id, friend_id):
    user = db.session.query(User).filter(User.id == id).first()
    friend = db.session.query(User).filter(User.id == friend_id).first()
    
    if user.incoming_friend_requests.count(friend) == 0:
        return jsonify({
                "status": 400,
                "message": "Error: Friend request does not exist.",
                "data": {}
            })

    user.incoming_friend_requests.remove(friend)
    db.session.commit()

    friend.outgoing_friend_requests.remove(user)
    db.session.commit()

    return jsonify({
        "status": 200,
        "message": "Friend Request Deleted",
        "data": {
            "user": user_schema.dump(user),
            "friend": user_schema.dump(friend)
        }
    })

@app.route("/user/friend/delete/<id>/<friend_id>", methods=["DELETE"])
def delete_friend(id, friend_id):
    user = db.session.query(User).filter(User.id == id).first()
    friend = db.session.query(User).filter(User.id == friend_id).first()
    
    if user.friends.count(friend) == 0:
        return jsonify({
                "status": 400,
                "message": "Error: Friend does not exist.",
                "data": {}
            })

    user.friends.remove(friend)
    db.session.commit()

    friend.friends.remove(user)
    db.session.commit()

    return jsonify({
        "status": 200,
        "message": "Friend Deleted",
        "data": {
            "user": user_schema.dump(user),
            "friend": user_schema.dump(friend)
        }
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
    difficulty = data.get("difficulty", 0)
    user_id = data.get("user_id")

    user = db.session.query(User).filter(User.id == user_id).first()

    record = Meal(name, description, image_url, difficulty, user.username, user_id)
    db.session.add(record)
    db.session.commit()

    recipe = Recipe(record.id)
    db.session.add(recipe)
    db.session.commit()

    return jsonify({
        "status": 200,
        "message": "Meal Added",
        "data": meal_schema.dump(record)
    })

@app.route("/meal/share", methods=["POST"])
def share_meal():
    if request.content_type != "application/json":
        return jsonify({
            "status": 400,
            "message": "Error: Data must be sent as JSON.",
            "data": {}
        })

    data = request.get_json()
    meal_id = data.get("meal_id")
    user_id = data.get("user_id")

    shared_user = db.session.query(User).filter(User.id == user_id).first()
    shared_meal = db.session.query(Meal).filter(Meal.id == meal_id).first()

    shared_user.shared_meals.append(shared_meal)
    db.session.commit()

    return jsonify({
        "status": 200,
        "message": "Meal Shared",
        "data": {
            "meal": meal_schema.dump(shared_meal),
            "user": user_schema.dump(shared_user)
        }
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
    difficulty = data.get("difficulty")
    image_url = data.get("image_url")
    sleep_until = data.get("sleep_until")

    record = db.session.query(Meal).filter(Meal.id == id).first()
    if name is not None:
        record.name = name
    if description is not None:
        record.description = description
    if image_url is not None:
        record.image_url = image_url
    if difficulty is not None:
        record.difficulty = difficulty
    if sleep_until is not None:
        record.sleep_until = sleep_until

    db.session.commit()

    return jsonify({
        "status": 200,
        "message": "Meal Updated",
        "data": meal_schema.dump(record)
    })

@app.route("/meal/delete/<id>", methods=["DELETE"])
def delete_meal(id):
    record = db.session.query(Meal).filter(Meal.id == id).first()
    for user in record.shared_users:
        user.shared_meals.remove(record)
        db.session.commit()
    db.session.delete(record)
    db.session.commit()
    return jsonify({
        "status": 200,
        "message": "Meal Deleted",
        "data": meal_schema.dump(record)
    })

@app.route("/meal/unshare/<id>/<user_id>", methods=["DELETE"])
def unshare_meal(id, user_id):
    record = db.session.query(Meal).filter(Meal.id == id).first()
    shared_user = db.session.query(User).filter(User.id == user_id).first()

    if shared_user.shared_meals.count(record) == 0:
        return jsonify({
                "status": 400,
                "message": "Error: Shared meal does not exist.",
                "data": {}
            })

    shared_user.shared_meals.remove(record)
    db.session.commit()
    return jsonify({
        "status": 200,
        "message": "Meal Share Deleted",
        "data":{
            "meal": meal_schema.dump(record),
            "user": user_schema.dump(shared_user)
        }
    })


@app.route("/category/add", methods=["POST"])
def add_category():
    if request.content_type != "application/json":
        return jsonify({
            "status": 400,
            "message": "Error: Data must be sent as JSON.",
            "data": {}
        })

    data = request.get_json()
    name = data.get("name")
    user_id = data.get("user_id")

    record = Category(name, user_id)
    db.session.add(record)
    db.session.commit()

    return jsonify({
        "status": 200,
        "message": "Category Added",
        "data": category_schema.dump(record)
    })

@app.route("/category/add/multiple", methods=["POST"])
def add_multiple_categories():
    if request.content_type != "application/json":
        return jsonify({
            "status": 400,
            "message": "Error: Data must be sent as JSON.",
            "data": {}
        })

    data = request.get_json()
    records = []
    for data in data:
        name = data.get("name")
        user_id = data.get("user_id")

        record = Category(name, user_id)
        db.session.add(record)
        db.session.commit()

        records.append(record)

    return jsonify({
        "status": 200,
        "message": "Categories Added",
        "data": multiple_category_schema.dump(records)
    })

@app.route("/category/attach", methods=["POST"])
def attach_category():
    if request.content_type != "application/json":
        return jsonify({
            "status": 400,
            "message": "Error: Data must be sent as JSON.",
            "data": {}
        })

    data = request.get_json()
    category_id = data.get("category_id")
    meal_id = data.get("meal_id")

    record = db.session.query(Category).filter(Category.id == category_id).first()
    meal = db.session.query(Meal).filter(Meal.id == meal_id).first()
    meal.categories.append(record)
    db.session.commit()

    return jsonify({
        "status": 200,
        "message": "Category Attached",
        "data": {
            "category": category_schema.dump(record),
            "meal": meal_schema.dump(meal)
        }
    })

@app.route("/category/attach/multiple", methods=["POST"])
def attach_multiple_categories():
    if request.content_type != "application/json":
        return jsonify({
            "status": 400,
            "message": "Error: Data must be sent as JSON.",
            "data": {}
        })

    data = request.get_json()

    records = []
    meals = []
    print(data)
    for data in data:
        print(data)
        category_id = data.get("category_id")
        meal_id = data.get("meal_id")

        record = db.session.query(Category).filter(Category.id == category_id).first()
        meal = db.session.query(Meal).filter(Meal.id == meal_id).first()
        meal.categories.append(record)
        db.session.commit()

        records.append(record)
        meals.append(meal)

    return jsonify({
        "status": 200,
        "message": "Category Attached",
        "data": {
            "categories": multiple_category_schema.dump(records),
            "meals": multiple_meal_schema.dump(meals)
        }
    })

@app.route("/category/get", methods=["GET"])
def get_all_categories():
    records = db.session.query(Category).all()
    return jsonify(multiple_category_schema.dump(records))

@app.route("/category/get/<id>", methods=["GET"])
def get_category_by_id(id):
    record = db.session.query(Category).filter(Category.id == id).first()
    return jsonify(category_schema.dump(record))

@app.route("/category/update/<id>", methods=["PUT"])
def update_category(id):
    if request.content_type != "application/json":
        return jsonify({
            "status": 400,
            "message": "Error: Data must be sent as JSON.",
            "data": {}
        })

    data = request.get_json()
    name = data.get("name")

    record = db.session.query(Category).filter(Category.id == id).first()
    if name is not None:
        record.name = name

    db.session.commit()

    return jsonify({
        "status": 200,
        "message": "Category Updated",
        "data": category_schema.dump(record)
    })

@app.route("/category/delete/<id>", methods=["DELETE"])
def delete_category(id):
    record = db.session.query(Category).filter(Category.id == id).first()
    db.session.delete(record)
    db.session.commit()
    return jsonify({
        "status": 200,
        "message": "Category Deleted",
        "data": category_schema.dump(record)
    })


@app.route("/recipe/add", methods=["POST"])
def add_recipe():
    if request.content_type != "application/json":
        return jsonify({
            "status": 400,
            "message": "Error: Data must be sent as JSON.",
            "data": {}
        })

    data = request.get_json()
    meal_id = data.get("meal_id")

    recipe_check = db.session.query(Recipe).filter(Recipe.meal_id == meal_id).first()
    if recipe_check is not None:
        return jsonify({
            "status": 400,
            "message": "Error: Recipe already exists.",
            "data": {}
        })

    record = Recipe(meal_id)
    db.session.add(record)
    db.session.commit()

    return jsonify({
        "status": 200,
        "message": "Recipe Added",
        "data": recipe_schema.dump(record)
    })

@app.route("/recipe/get", methods=["GET"])
def get_all_recipes():
    records = db.session.query(Recipe).all()
    return jsonify(multiple_recipe_schema.dump(records))

@app.route("/recipe/get/<id>", methods=["GET"])
def get_recipe_by_id(id):
    record = db.session.query(Recipe).filter(Recipe.id == id).first()
    return jsonify(meal_schema.dump(record))

@app.route("/recipe/delete/<id>", methods=["DELETE"])
def delete_recipe(id):
    record = db.session.query(Recipe).filter(Recipe.id == id).first()
    db.session.delete(record)
    db.session.commit()
    return jsonify({
        "status": 200,
        "message": "Recipe Deleted",
        "data": recipe_schema.dump(record)
    })


@app.route("/stepsection/add", methods=["POST"])
def add_stepsection():
    if request.content_type != "application/json":
        return jsonify({
            "status": 400,
            "message": "Error: Data must be sent as JSON.",
            "data": {}
        })

    data = request.get_json()
    title = data.get("title")
    recipe_id = data.get("recipe_id")

    record = Stepsection(title, recipe_id)
    db.session.add(record)
    db.session.commit()

    return jsonify({
        "status": 200,
        "message": "Stepsection Added",
        "data": stepsection_schema.dump(record)
    })

@app.route("/stepsection/add/multiple", methods=["POST"])
def add_multiple_stepsections():
    if request.content_type != "application/json":
        return jsonify({
            "status": 400,
            "message": "Error: Data must be sent as JSON.",
            "data": {}
        })

    data = request.get_json()
    records = []
    for data in data:
        title = data.get("title")
        recipe_id = data.get("recipe_id")

        record = Stepsection(title, recipe_id)
        db.session.add(record)
        db.session.commit()

        records.append(record)

    return jsonify({
        "status": 200,
        "message": "Stepsections Added",
        "data": multiple_stepsection_schema.dump(records)
    })

@app.route("/stepsection/get", methods=["GET"])
def get_all_stepsections():
    records = db.session.query(Stepsection).all()
    return jsonify(multiple_stepsection_schema.dump(records))

@app.route("/stepsection/get/<id>", methods=["GET"])
def get_stepsection_by_id(id):
    record = db.session.query(Stepsection).filter(Stepsection.id == id).first()
    return jsonify(stepsection_schema.dump(record))

@app.route("/stepsection/update/<id>", methods=["PUT"])
def update_stepsection(id):
    if request.content_type != "application/json":
        return jsonify({
            "status": 400,
            "message": "Error: Data must be sent as JSON.",
            "data": {}
        })

    data = request.get_json()
    title = data.get("title")

    record = db.session.query(Stepsection).filter(Step.id == id).first()
    if title is not None:
        record.title = title

    db.session.commit()

    return jsonify({
        "status": 200,
        "message": "Stepsection Updated",
        "data": stepsection_schema.dump(record)
    })

@app.route("/stepsection/delete/<id>", methods=["DELETE"])
def delete_stepsection(id):
    record = db.session.query(Stepsection).filter(Stepsection.id == id).first()
    db.session.delete(record)
    db.session.commit()
    return jsonify({
        "status": 200,
        "message": "Stepsection Deleted",
        "data": stepsection_schema.dump(record)
    })


@app.route("/step/add", methods=["POST"])
def add_step():
    if request.content_type != "application/json":
        return jsonify({
            "status": 400,
            "message": "Error: Data must be sent as JSON.",
            "data": {}
        })

    data = request.get_json()
    number = data.get("number")
    text = data.get("text")
    recipe_id = data.get("recipe_id")
    stepsection_id = data.get("stepsection_id")

    record = Step(number, text, recipe_id, stepsection_id)
    db.session.add(record)
    db.session.commit()

    return jsonify({
        "status": 200,
        "message": "Step Added",
        "data": step_schema.dump(record)
    })

@app.route("/step/add/multiple", methods=["POST"])
def add_multiple_steps():
    if request.content_type != "application/json":
        return jsonify({
            "status": 400,
            "message": "Error: Data must be sent as JSON.",
            "data": {}
        })

    data = request.get_json()
    records = []
    for data in data:
        number = data.get("number")
        text = data.get("text")
        recipe_id = data.get("recipe_id")
        stepsection_id = data.get("stepsection_id")

        record = Step(number, text, recipe_id, stepsection_id)
        db.session.add(record)
        db.session.commit()

        records.append(record)

    return jsonify({
        "status": 200,
        "message": "Steps Added",
        "data": multiple_step_schema.dump(records)
    })

@app.route("/step/get", methods=["GET"])
def get_all_steps():
    records = db.session.query(Step).all()
    return jsonify(multiple_step_schema.dump(records))

@app.route("/step/get/<id>", methods=["GET"])
def get_step_by_id(id):
    record = db.session.query(Step).filter(Step.id == id).first()
    return jsonify(step_schema.dump(record))

@app.route("/step/update/<id>", methods=["PUT"])
def update_step(id):
    if request.content_type != "application/json":
        return jsonify({
            "status": 400,
            "message": "Error: Data must be sent as JSON.",
            "data": {}
        })

    data = request.get_json()
    number = data.get("number")
    text = data.get("text")

    record = db.session.query(Step).filter(Step.id == id).first()
    if number is not None:
        record.number = number
    if text is not None:
        record.text = text

    db.session.commit()

    return jsonify({
        "status": 200,
        "message": "Step Updated",
        "data": step_schema.dump(record)
    })

@app.route("/step/delete/<id>", methods=["DELETE"])
def delete_step(id):
    record = db.session.query(Step).filter(Step.id == id).first()
    db.session.delete(record)
    db.session.commit()
    return jsonify({
        "status": 200,
        "message": "Step Deleted",
        "data": step_schema.dump(record)
    })


@app.route("/ingredient/add", methods=["POST"])
def add_ingredient():
    if request.content_type != "application/json":
        return jsonify({
            "status": 400,
            "message": "Error: Data must be sent as JSON.",
            "data": {}
        })

    data = request.get_json()
    name = data.get("name")
    amount = data.get("amount")
    category = data.get("category")
    recipe_id = data.get("recipe_id")

    record = Ingredient(name, amount, category, recipe_id)
    db.session.add(record)
    db.session.commit()

    meal = db.session.query(Meal).join(Recipe).filter(Recipe.id == record.recipe_id).first()
    for mealplan in meal.mealplans:
        if mealplan.shoppinglist is not None:
            shoppingingredient = Shoppingingredient(name, amount, category, meal.name, mealplan.shoppinglist[0].id, record.id)
            db.session.add(shoppingingredient)
            db.session.commit()

    return jsonify({
        "status": 200,
        "message": "Ingredient Added",
        "data": ingredient_schema.dump(record)
    })

@app.route("/ingredient/add/multiple", methods=["POST"])
def add_multiple_ingredients():
    if request.content_type != "application/json":
        return jsonify({
            "status": 400,
            "message": "Error: Data must be sent as JSON.",
            "data": {}
        })

    data = request.get_json()
    records = []
    for data in data:
        name = data.get("name")
        amount = data.get("amount")
        category = data.get("category")
        recipe_id = data.get("recipe_id")

        record = Ingredient(name, amount, category, recipe_id)
        db.session.add(record)
        db.session.commit()

        records.append(record)

        meal = db.session.query(Meal).join(Recipe).filter(Recipe.id == record.recipe_id).first()
        for mealplan in meal.mealplans:
            if mealplan.shoppinglist is not None:
                shoppingingredient = Shoppingingredient(name, amount, category, meal.name, mealplan.shoppinglist[0].id, record.id)
                db.session.add(shoppingingredient)
                db.session.commit()

    return jsonify({
        "status": 200,
        "message": "Ingredients Added",
        "data": multiple_ingredient_schema.dump(records)
    })

@app.route("/ingredient/get", methods=["GET"])
def get_all_ingredients():
    records = db.session.query(Ingredient).all()
    return jsonify(multiple_ingredient_schema.dump(records))

@app.route("/ingredient/get/<id>", methods=["GET"])
def get_ingredient_by_id(id):
    record = db.session.query(Ingredient).filter(Ingredient.id == id).first()
    return jsonify(ingredient_schema.dump(record))

@app.route("/ingredient/update/<id>", methods=["PUT"])
def update_ingredient(id):
    if request.content_type != "application/json":
        return jsonify({
            "status": 400,
            "message": "Error: Data must be sent as JSON.",
            "data": {}
        })

    data = request.get_json()
    name = data.get("name")
    amount = data.get("amount")
    category = data.get("category")

    record = db.session.query(Ingredient).filter(Ingredient.id == id).first()
    if name is not None:
        record.name = name
        for shoppingingredient in record.shoppingingredients:
            shoppingingredient.name = name
            db.session.commit()
    if amount is not None:
        record.amount = amount
        for shoppingingredient in record.shoppingingredients:
            shoppingingredient.amount = amount
            db.session.commit()
    if category is not None:
        record.category = category
        for shoppingingredient in record.shoppingingredients:
            shoppingingredient.category = category
            db.session.commit()

    db.session.commit()

    return jsonify({
        "status": 200,
        "message": "Ingredient Updated",
        "data": ingredient_schema.dump(record)
    })

@app.route("/ingredient/delete/<id>", methods=["DELETE"])
def delete_ingredient(id):
    record = db.session.query(Ingredient).filter(Ingredient.id == id).first()
    db.session.delete(record)
    db.session.commit()

    for shoppingingredient in record.shoppingingredients:
        db.session.delete(shoppingingredient)
        db.session.commit()

    return jsonify({
        "status": 200,
        "message": "Ingredient Deleted",
        "data": ingredient_schema.dump(record)
    })


@app.route("/mealplan/add", methods=["POST"])
def add_mealplan():
    if request.content_type != "application/json":
        return jsonify({
            "status": 400,
            "message": "Error: Data must be sent as JSON.",
            "data": {}
        })

    data = request.get_json()
    name = data.get("name")
    created_on = data.get("created_on")
    user_username = data.get("user_username")
    user_id = data.get("user_id")
    meals = data.get("meals")

    record = Mealplan(name, created_on, user_username, user_id)
    db.session.add(record)
    db.session.commit()

    shoppinglist = Shoppinglist(f"{name} Mealplan", created_on, False, user_id, record.id)
    db.session.add(shoppinglist)
    db.session.commit()

    for meal_id in meals:
        meal = db.session.query(Meal).filter(Meal.id == meal_id).first()
        record.meals.append(meal)
        db.session.commit()

        for ingredient in meal.recipe[0].ingredients:
            shoppingingredient = Shoppingingredient(ingredient.name, ingredient.amount, ingredient.category, meal.name, shoppinglist.id, ingredient.id)
            db.session.add(shoppingingredient)
            db.session.commit()

    return jsonify({
        "status": 200,
        "message": "Mealplan Added",
        "data": mealplan_schema.dump(record)
    })

@app.route("/mealplan/share", methods=["POST"])
def share_mealplan():
    if request.content_type != "application/json":
        return jsonify({
            "status": 400,
            "message": "Error: Data must be sent as JSON.",
            "data": {}
        })

    data = request.get_json()
    mealplan_id = data.get("mealplan_id")
    user_id = data.get("user_id")

    shared_user = db.session.query(User).filter(User.id == user_id).first()
    shared_mealplan = db.session.query(Mealplan).filter(Mealplan.id == mealplan_id).first()

    shared_user.shared_mealplans.append(shared_mealplan)
    db.session.commit()

    if len(shared_mealplan.shoppinglist) > 0:
        shared_user.shared_shoppinglists.append(shared_mealplan.shoppinglist[0])
        db.session.commit()

    return jsonify({
        "status": 200,
        "message": "Mealplan Shared",
        "data": {
            "mealplan": mealplan_schema.dump(shared_mealplan),
            "user": user_schema.dump(shared_user)
        }
    })

@app.route("/mealplan/meal/add", methods=["POST"])
def add_meal_to_mealplan():
    if request.content_type != "application/json":
        return jsonify({
            "status": 400,
            "message": "Error: Data must be sent as JSON.",
            "data": {}
        })

    data = request.get_json()
    mealplan_id = data.get("mealplan_id")
    meal_id = data.get("meal_id")

    record = db.session.query(Mealplan).filter(Mealplan.id == mealplan_id).first()
    meal = db.session.query(Meal).filter(Meal.id == meal_id).first()
    
    record.meals.append(meal)
    db.session.commit()

    for ingredient in meal.recipe[0].ingredients:
        shoppingingredient = Shoppingingredient(ingredient.name, ingredient.amount, ingredient.category, meal.name, record.shoppinglist[0].id, ingredient.id)
        db.session.add(shoppingingredient)
        db.session.commit()

    return jsonify({
        "status": 200,
        "message": "Meal added to mealplan",
        "data": {
            "mealplan": mealplan_schema.dump(record),
            "meal": meal_schema.dump(meal)
        }
    })

@app.route("/mealplan/get", methods=["GET"])
def get_all_mealplans():
    records = db.session.query(Mealplan).all()
    return jsonify(multiple_mealplan_schema.dump(records))

@app.route("/mealplan/get/<id>", methods=["GET"])
def get_mealplan_by_id(id):
    record = db.session.query(Mealplan).filter(Mealplan.id == id).first()
    return jsonify(mealplan_schema.dump(record))

@app.route("/mealplan/update/<id>", methods=["PUT"])
def update_mealplan(id):
    if request.content_type != "application/json":
        return jsonify({
            "status": 400,
            "message": "Error: Data must be sent as JSON.",
            "data": {}
        })

    data = request.get_json()
    name = data.get("name")

    record = db.session.query(Mealplan).filter(Mealplan.id == id).first()
    if name is not None:
        record.name = name
        record.shoppinglist[0].name = f"{name} Mealplan"

    db.session.commit()

    return jsonify({
        "status": 200,
        "message": "Mealplan Updated",
        "data": mealplan_schema.dump(record)
    })

@app.route("/mealplan/delete/<id>", methods=["DELETE"])
def delete_mealplan(id):
    record = db.session.query(Mealplan).filter(Mealplan.id == id).first()
    for user in record.shared_users:
        user.shared_mealplans.remove(record)
        db.session.commit()
    db.session.delete(record)
    db.session.commit()
    return jsonify({
        "status": 200,
        "message": "Mealplan Deleted",
        "data": mealplan_schema.dump(record)
    })

@app.route("/mealplan/unshare/<id>/<user_id>", methods=["DELETE"])
def unshare_mealplan(id, user_id):
    record = db.session.query(Mealplan).filter(Mealplan.id == id).first()
    shared_user = db.session.query(User).filter(User.id == user_id).first()

    if shared_user.shared_mealplans.count(record) == 0:
        return jsonify({
                "status": 400,
                "message": "Error: Shared mealplan does not exist.",
                "data": {}
            })

    shared_user.shared_mealplans.remove(record)
    db.session.commit()

    if len(record.shoppinglist) > 0:
        shared_user.shared_shoppinglists.remove(record.shoppinglist)
        db.session.commit()

    return jsonify({
        "status": 200,
        "message": "Mealplan Share Deleted",
        "data":{
            "meal": mealplan_schema.dump(record),
            "user": user_schema.dump(shared_user)
        }
    })

@app.route("/mealplan/meal/delete", methods=["DELETE"])
def delete_meal_from_mealplan():
    if request.content_type != "application/json":
        return jsonify({
            "status": 400,
            "message": "Error: Data must be sent as JSON.",
            "data": {}
        })

    data = request.get_json()
    mealplan_id = data.get("mealplan_id")
    meal_id = data.get("meal_id")

    record = db.session.query(Mealplan).filter(Mealplan.id == mealplan_id).first()
    meal = db.session.query(Meal).filter(Meal.id == meal_id).first()
    
    record.meals.remove(meal)
    db.session.commit()

    for ingredient in meal.recipe[0].ingredients:
        for shoppingingredient in ingredient.shoppingingredients:
            if shoppingingredient.shoppinglist_id == record.shoppinglist[0].id:
                db.session.delete(shoppingingredient)
                db.session.commit()

    return jsonify({
        "status": 200,
        "message": "Meal deleted from mealplan",
        "data": {
            "mealplan": mealplan_schema.dump(record),
            "meal": meal_schema.dump(meal)
        }
    })


@app.route("/shoppinglist/add", methods=["POST"])
def add_shoppinglist():
    if request.content_type != "application/json":
        return jsonify({
            "status": 400,
            "message": "Error: Data must be sent as JSON.",
            "data": {}
        })

    data = request.get_json()
    name = data.get("name")
    created_on = data.get("created_on")
    updates_hidden = data.get("updates_hidden")
    user_id = data.get("user_id")
    mealplan_id = data.get("mealplan_id")

    record = Shoppinglist(name, created_on, updates_hidden, user_id, mealplan_id)
    db.session.add(record)
    db.session.commit()

    if mealplan_id is not None:
        mealplan = db.session.query(Mealplan).filter(Mealplan.id == mealplan_id).first()
        for user in mealplan.shared_users:
            user.shared_shoppinglists.append(record)
            db.session.commit()

    return jsonify({
        "status": 200,
        "message": "Shoppinglist Added",
        "data": shoppinglist_schema.dump(record)
    })

@app.route("/shoppinglist/share", methods=["POST"])
def share_shoppinglist():
    if request.content_type != "application/json":
        return jsonify({
            "status": 400,
            "message": "Error: Data must be sent as JSON.",
            "data": {}
        })

    data = request.get_json()
    shoppinglist_id = data.get("shoppinglist_id")
    user_id = data.get("user_id")

    shared_user = db.session.query(User).filter(User.id == user_id).first()
    shared_shoppinglist = db.session.query(Shoppinglist).filter(Shoppinglist.id == shoppinglist_id).first()

    shared_user.shared_shoppinglists.append(shared_shoppinglist)
    db.session.commit()

    return jsonify({
        "status": 200,
        "message": "Shoppinglist Shared",
        "data": {
            "shoppinglist": shoppinglist_schema.dump(shared_shoppinglist),
            "user": user_schema.dump(shared_user)
        }
    })

@app.route("/shoppinglist/get", methods=["GET"])
def get_all_shoppinglists():
    records = db.session.query(Shoppinglist).all()
    return jsonify(multiple_shoppinglist_schema.dump(records))

@app.route("/shoppinglist/get/<id>", methods=["GET"])
def get_shoppinglist_by_id(id):
    record = db.session.query(Shoppinglist).filter(Shoppinglist.id == id).first()
    return jsonify(shoppinglist_schema.dump(record))

@app.route("/shoppinglist/update/<id>", methods=["PUT"])
def update_shoppinglist(id):
    if request.content_type != "application/json":
        return jsonify({
            "status": 400,
            "message": "Error: Data must be sent as JSON.",
            "data": {}
        })

    data = request.get_json()
    name = data.get("name")
    updates_hidden = data.get("updates_hidden")

    record = db.session.query(Shoppinglist).filter(Shoppinglist.id == id).first()
    if name is not None:
        record.name = name
    if updates_hidden is not None:
        record.updates_hidden = updates_hidden

    db.session.commit()

    return jsonify({
        "status": 200,
        "message": "Shoppinglist Updated",
        "data": shoppinglist_schema.dump(record)
    })

@app.route("/shoppinglist/delete/<id>", methods=["DELETE"])
def delete_shoppinglist(id):
    record = db.session.query(Shoppinglist).filter(Shoppinglist.id == id).first()
    for user in record.shared_users:
        user.shared_shoppinglists.remove(record)
        db.session.commit()
    db.session.delete(record)
    db.session.commit()
    return jsonify({
        "status": 200,
        "message": "Shoppinglist Deleted",
        "data": shoppinglist_schema.dump(record)
    })

@app.route("/shoppinglist/unshare/<id>/<user_id>", methods=["DELETE"])
def unshare_shoppinglist(id, user_id):
    record = db.session.query(Shoppinglist).filter(Shoppinglist.id == id).first()
    shared_user = db.session.query(User).filter(User.id == user_id).first()

    if shared_user.shared_shoppinglists.count(record) == 0:
        return jsonify({
                "status": 400,
                "message": "Error: Shared shoppinglist does not exist.",
                "data": {}
            })

    shared_user.shared_shoppinglists.remove(record)
    db.session.commit()
    return jsonify({
        "status": 200,
        "message": "Shoppinglist Share Deleted",
        "data":{
            "meal": shoppinglist_schema.dump(record),
            "user": user_schema.dump(shared_user)
        }
    })


@app.route("/shoppingingredient/add", methods=["POST"])
def add_shoppingingredient():
    if request.content_type != "application/json":
        return jsonify({
            "status": 400,
            "message": "Error: Data must be sent as JSON.",
            "data": {}
        })

    data = request.get_json()
    name = data.get("name")
    amount = data.get("amount")
    category = data.get("category")
    meal_name = data.get("meal_name")
    shoppinglist_id = data.get("shoppinglist_id")
    ingredient_id = data.get("ingredient_id")

    record = Shoppingingredient(name, amount, category, meal_name, shoppinglist_id, ingredient_id)
    db.session.add(record)
    db.session.commit()

    return jsonify({
        "status": 200,
        "message": "Shoppingingredient Added",
        "data": shoppingingredient_schema.dump(record)
    })

@app.route("/shoppingingredient/add/multiple", methods=["POST"])
def add_multiple_shoppingingredients():
    if request.content_type != "application/json":
        return jsonify({
            "status": 400,
            "message": "Error: Data must be sent as JSON.",
            "data": {}
        })

    data = request.get_json()
    records = []
    for data in data:
        name = data.get("name")
        amount = data.get("amount")
        category = data.get("category")
        meal_name = data.get("meal_name")
        shoppinglist_id = data.get("shoppinglist_id")
        ingredient_id = data.get("ingredient_id")

        record = Shoppingingredient(name, amount, category, meal_name, shoppinglist_id, ingredient_id)
        db.session.add(record)
        db.session.commit()

        records.append(record)

    return jsonify({
        "status": 200,
        "message": "Shoppingingredients Added",
        "data": multiple_shoppingingredient_schema.dump(records)
    })

@app.route("/shoppingingredient/get", methods=["GET"])
def get_all_shoppingingredients():
    records = db.session.query(Shoppingingredient).all()
    return jsonify(multiple_shoppingingredient_schema.dump(records))

@app.route("/shoppingingredient/get/<id>", methods=["GET"])
def get_shoppingingredient_by_id(id):
    record = db.session.query(Shoppingingredient).filter(Shoppingingredient.id == id).first()
    return jsonify(ingredient_schema.dump(record))

@app.route("/shoppingingredient/update/<id>", methods=["PUT"])
def update_shoppingingredient(id):
    if request.content_type != "application/json":
        return jsonify({
            "status": 400,
            "message": "Error: Data must be sent as JSON.",
            "data": {}
        })

    data = request.get_json()
    name = data.get("name")
    amount = data.get("amount")
    category = data.get("category")
    obtained = data.get("obtained")
    meal_name = data.get("meal_name")

    record = db.session.query(Shoppingingredient).filter(Shoppingingredient.id == id).first()
    if name is not None:
        record.name = name
    if amount is not None:
        record.amount = amount
    if category is not None:
        record.category = category
    if obtained is not None:
        record.obtained = obtained
    if meal_name is not None:
        record.meal_name = meal_name

    db.session.commit()

    return jsonify({
        "status": 200,
        "message": "Shoppingingredient Updated",
        "data": shoppingingredient_schema.dump(record)
    })

@app.route("/shoppingingredient/delete/<id>", methods=["DELETE"])
def delete_shoppingingredient(id):
    record = db.session.query(Shoppingingredient).filter(Shoppingingredient.id == id).first()
    db.session.delete(record)
    db.session.commit()
    return jsonify({
        "status": 200,
        "message": "Shoppingingredient Deleted",
        "data": shoppingingredient_schema.dump(record)
    })

if __name__ == "__main__":
    app.run(debug=True)
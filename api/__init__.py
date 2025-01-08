from flask import Flask
from flask_restx import Api
from .orders.views import order_namespace
from .auth.views import auth_namespace
from .config.config import config_dict
from .utils import db
from .models.orders import Order , Resource as ResourceModel
from .models.users import User
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from werkzeug.exceptions import NotFound, MethodNotAllowed


 
def create_app(config=config_dict['dev']):
    app = Flask(__name__)

    app.config.from_object(config)
    authorizations={
        "Bearer Auth":{
            'type':"apiKey",
            'in':'header',
            'name':"Authorization",
            'description':"Add a JWT with ** Bearer &lt;JWT&gt; to authorize"
        }
    }
    api = Api(app , title="OnePiece Hoodies API",
              description = "A REST API for a custom hoodie application, where clients can choose hoodie color, design, size, material (cotton, polyester, etc.), quantity, and other customization options inspired by the One Piece universe ",
              authorizations= authorizations,
              security= "Bearer Auth"
              )
    api.add_namespace(order_namespace)
    api.add_namespace(auth_namespace, path='/auth')
    db.init_app(app)

    jwt = JWTManager(app)

    migrate = Migrate(app, db)


    ##costum error handler
    @api.errorhandler(NotFound)
    def not_found(error):
        return {"error" : "Not Found"}, 404
    

    @api.errorhandler(MethodNotAllowed)
    def method_not_allowed(error):
        return {"error" : "Method Not Allowed"}, 405

    

    @app.shell_context_processor
    def make_shell_context():
        return {
            'db': db,
            'User': User,
            'Order' : Order,
            'Resource' : ResourceModel
        }

    return app

##costum error handler
from flask_restx import Namespace, Resource, fields
from flask import request
from ..models.users import User
from werkzeug.security import generate_password_hash , check_password_hash
from http import HTTPStatus
from flask_jwt_extended import (create_access_token , create_refresh_token, jwt_required, get_jwt_identity)
from werkzeug.exceptions import Conflict , BadRequest

auth_namespace = Namespace('auth', description="a name space for authentication")


signup_model = auth_namespace.model(
    'SignUp' , {
        'id': fields.Integer(),
        'userName': fields.String(required=True, description='the user name'),
        'Email': fields.String(required=True, description='the email'),
        'password': fields.String(required=True, description='the password'),
        'role': fields.String(required=True, description='the user role', enum=['ADMIN', 'CLIENT'])
    }
)

user_model=auth_namespace.model(
    'User', {
        'id': fields.Integer(),
        'userName': fields.String(required=True, description='the user name'),
        'Email': fields.String(required=True, description='the email'),
        'password': fields.String(required=True, description='the password'),
        'role': fields.String(required=True, description='the user role'),
        'is_active': fields.Boolean(description="User is active"),
        'is_staff': fields.Boolean(description='User is staff')
    }
)

login_model = auth_namespace.model(
    'Login', {
        'Email': fields.String(required=True, description="an email" ),
        'password' :fields.String(required=True, description="the password")
    }
)



@auth_namespace.route('/signup')
class SignUp(Resource):

    @auth_namespace.expect(signup_model)
    @auth_namespace.marshal_with(user_model)
    def post(self):
        """
            Create a new user
        """
        data = request.get_json()

        #handle the error that : if the user is already exist
        try:
            new_user = User(
                userName = data.get('userName'),
                Email=data.get('Email'),
                password=generate_password_hash(data.get('password')),
                role=data.get('role', 'CLIENT')
            )
        
            new_user.save()

            return new_user, HTTPStatus.CREATED
        
        except Exception as e :
            raise Conflict(f"User with the email : {data.get('Email')}  already exists")
            


        


@auth_namespace.route('/login')
class Login(Resource):

    @auth_namespace.expect(login_model)
    def post(self):
        """
            Generate a JWT pair 
        """

        data = request.get_json()
        Email = data.get('Email')
        password = data.get('password')
        user = User.query.filter_by(Email=Email).first()
        

        if user is not None and check_password_hash(user.password,password):
            access_token = create_access_token(identity=user.userName)
            refresh_token = create_refresh_token(identity=user.userName)

            response = {
                'access_token': access_token,
                'refresh_token' : refresh_token,
                'userName': user.userName,
                'is-staff' : user.is_staff
            }

            return response , HTTPStatus.OK
        

        raise BadRequest("Invalid UserName or Password")



@auth_namespace.route('/refresh')
class Refresh(Resource):

    @jwt_required(refresh=True)
    def post(self):
        userName = get_jwt_identity()

        access_token = create_access_token(identity=userName)

        return {"access_token" : access_token}, HTTPStatus.OK

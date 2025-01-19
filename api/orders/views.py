from flask import session
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models.orders import Order, Resource as ResourceModel
from ..models.users import User
from http import HTTPStatus
from ..utils.__init__ import db
from datetime import datetime

order_namespace = Namespace('orders', description="a name space for orders")


order_model=order_namespace.model(
    'Order', {
        'id':fields.Integer(description='The Id'),
        'quantity':fields.Integer(description='The quantity'),
        'size' : fields.String(description="the size of the hoodie", required=True,
                               enum=['SMALL','MEDIUM','LARGE','EXTRA_LARGE']),
        'order_status' : fields.String(description="the status of the hoodie", required=True,
                               enum=['PENDING','IN_PROGRESS','SHIPPED','DELIVERED','CANCELED','RETURNED']),
        'color' : fields.String(description="the color of the hoodie", required=True,
                               enum=['RED', 'BLUE', 'BLACK', 'WHITE', 'PINK','PURPLE', 'GREEN']),
        'design' : fields.String(description="the design of the hoodie", required=True,
                               enum=['STRAW_HAT_JOLLY_ROGER','RORONOA_ZORO_SWORDS','GOING_MERRY',
                                      'THOUSAND_SUNNY','MONKEY_D_LUFFY','PIRATE_KING', 'WANTED_POSTER']),
        'material' : fields.String(description="the size of the hoodie", required=True,
                               enum=['COTTON','POLYSTER','MIXED']),
        'date_created': fields.DateTime(description="The date the order was created"),
        'date_updated': fields.DateTime(description="The date the order was last updated"),
        

    }
)


order_status_model = order_namespace.model(
    'OrderStatus' , {
        'order_status' : fields.String(required=True, description = "Order Status",
                                       enum = ['PENDING','IN_PROGRESS','SHIPPED','DELIVERED','CANCELED','RETURNED'])
    }
)

resource_model = order_namespace.model(
    'Resource', {
        'id': fields.Integer(description='The Id'),
        'type': fields.String(description="The type of resource", required=True, enum=['MATERIAL', 'COLOR']),
        'name': fields.String(description="The name of the resource", required=True),
        'quantity': fields.Integer(description="The available quantity of the resource", required=True),
    }
)





@order_namespace.route('/')
class OrderGetCreate(Resource):

    @order_namespace.marshal_with(order_model)
    #for documentation
    @order_namespace.doc(
        description = "Retrieve all Orders"
    )
    @jwt_required()
    def get(self):
        """
            Get all the orders
        """

        user = User.query.filter_by(userName=get_jwt_identity()).first()
        if user.role == 'ADMIN':
            orders = Order.query.all()
        else:
            orders = Order.query.filter_by(user_id=user.id).all()
        return orders, HTTPStatus.OK



        #orders = Order.query.all()

        # orders, HTTPStatus.OK
    


    @order_namespace.expect(order_model)
    @order_namespace.marshal_with(order_model)
    @order_namespace.doc(
        description = "Adding new orders"
    )
    @jwt_required()
    def post(self):
        """
            Create a new order
        """

        userName = get_jwt_identity()
        current_user = User.query.filter_by(userName= userName).first()

        data = order_namespace.payload


        # Check if order is feasible
        color_resource = ResourceModel.query.filter_by(type='COLOR', name=data['color']).first()
        material_resource = ResourceModel.query.filter_by(type='MATERIAL', name=data['material']).first()

        if not color_resource or not material_resource or color_resource.quantity < data['quantity'] or material_resource.quantity < data['quantity']:
            return {"message": "Order not feasible due to resource constraints"}, HTTPStatus.BAD_REQUEST
        

        new_order = Order(
            size = data['size'],
            quantity = data['quantity'],
            color = data['color'],
            design = data['design'],
            material = data['material'],
            user_id=current_user.id
        )

        # Update resources
        color_resource.quantity -= data['quantity']
        material_resource.quantity -= data['quantity']

        #new_order.user = current_user.id #hna kot dayra .id
        #new_order.save()
        new_order.save()
        db.session.commit()

        return new_order , HTTPStatus.CREATED
    






@order_namespace.route('/<int:order_id>')
class GetUpdateDelete(Resource):
    
    @order_namespace.marshal_with(order_model)
    @order_namespace.doc(
        description = "Retrieve an Order by ID",
        parameters = {
            "order_id" : "an ID for an order"
        }
    )
    @jwt_required()
    def get(self, order_id):
        """
            Retriev an order by its id
        """

        user = User.query.filter_by(userName=get_jwt_identity()).first()
        order = Order.get_by_id(order_id)
        if user.role == 'ADMIN' or order.user_id == user.id:
            return order, HTTPStatus.OK
        return {"message": "You are not authorized to view this order"}, HTTPStatus.FORBIDDEN
        #order = Order.get_by_id(order_id)
        #return order, HTTPStatus.OK
    


    @order_namespace.expect(order_model)
    #@order_namespace.marshal_with(order_model)
    @order_namespace.doc(
        description = "Update an order given an ID"
    )
    @jwt_required()
    def put(self, order_id):
        """
            Update the order with id
        """

        try:
            user = User.query.filter_by(userName=get_jwt_identity()).first()
            order_to_update = Order.get_by_id(order_id)

            if not order_to_update:
                return {"message": "Order not found"}, HTTPStatus.NOT_FOUND

            if user.role != 'ADMIN' and order_to_update.user_id != user.id:
                return {"message": "You are not authorized to update this order"}, HTTPStatus.FORBIDDEN
            
            if order_to_update.order_status != 'PENDING':
                return {"message": "Only pending orders can be modified"}, HTTPStatus.BAD_REQUEST

            data = order_namespace.payload

            # Check if order is feasible
            color_resource = ResourceModel.query.filter_by(type='COLOR', name=data['color']).first()
            material_resource = ResourceModel.query.filter_by(type='MATERIAL', name=data['material']).first()

            if not color_resource or not material_resource:
                return {"message": "Invalid color or material"}, HTTPStatus.BAD_REQUEST

            quantity_diff = data['quantity'] - order_to_update.quantity
            if color_resource.quantity < quantity_diff or material_resource.quantity < quantity_diff:
                return {"message": "Order update not feasible due to resource constraints"}, HTTPStatus.BAD_REQUEST
            
            # Update resources
            color_resource.quantity -= quantity_diff
            material_resource.quantity -= quantity_diff

            # Update order
            order_to_update.quantity = data['quantity']
            order_to_update.size = data['size']
            order_to_update.color = data['color']
            order_to_update.design = data['design']
            order_to_update.material = data['material']
            order_to_update.date_updated = datetime.utcnow()

            db.session.commit()

            # Create response
            response = {
                "message": "Order updated successfully",
                "order": {
                    "id": order_to_update.id,
                    "quantity": order_to_update.quantity,
                    "size": order_to_update.size,
                    "order_status": order_to_update.order_status,
                    "color": order_to_update.color,
                    "design": order_to_update.design,
                    "material": order_to_update.material,
                    "date_created": str(order_to_update.date_created),
                    "date_updated": str(order_to_update.date_updated)
                }
            }

            return response, HTTPStatus.OK

        except Exception as e:
            db.session.rollback()
            return {"message": f"Error updating order: {str(e)}"}, HTTPStatus.INTERNAL_SERVER_ERROR


    #@order_namespace.marshal_with(order_model)
    @order_namespace.doc(
        description = "Delete an Order given the ID"
    )
    @jwt_required()
    def delete(self, order_id):
        """
            Delete an order with id
        """

        user = User.query.filter_by(userName=get_jwt_identity()).first()
        order_to_delete = session.query(Order).get(order_id)

        if user.role != 'ADMIN' and order_to_delete.user_id != user.id:
            return {"message": "You are not authorized to delete this order"}, HTTPStatus.FORBIDDEN

        #if order_to_delete.order_status != 'PENDING':
         #   return {"message": "Only pending orders can be deleted"}, HTTPStatus.BAD_REQUEST

        # Restore resources
        #color_resource = ResourceModel.query.filter_by(type='COLOR', name=order_to_delete.color).first()
        #material_resource = ResourceModel.query.filter_by(type='MATERIAL', name=order_to_delete.material).first()

        #color_resource.quantity += order_to_delete.quantity
        #material_resource.quantity += order_to_delete.quantity

        order_to_delete.delete()
        db.session.commit()

        return order_to_delete, HTTPStatus.NO_CONTENT




@order_namespace.route('/user/<int:user_id>/order/<int:order_id>')
class GetOrderById(Resource):

    @order_namespace.marshal_with(order_model)
    @order_namespace.doc(
        description = "Get a user's specific order"
    )
    @jwt_required()
    def get(self, user_id, order_id):
        """
            Get user's order
        """

        current_user = User.query.filter_by(userName=get_jwt_identity()).first()
        if current_user.role != 'ADMIN' and current_user.id != user_id:
            return {"message": "You are not authorized to view this order"}, HTTPStatus.FORBIDDEN

        order = Order.query.filter_by(id=order_id, user_id=user_id).first()
        if not order:
            return {"message": "Order not found"}, HTTPStatus.NOT_FOUND

        return order, HTTPStatus.OK



@order_namespace.route('/user/<int:user_id>/orders')
class UserOrders(Resource):

    @order_namespace.marshal_with(order_model)
    @order_namespace.doc(
        description = "Get the orders of a user given his ID"
    )
    @jwt_required()
    def get(self, user_id):
        """
            Get all orders of the user X
        """

        current_user = User.query.filter_by(userName=get_jwt_identity()).first()
        if current_user.role != 'ADMIN' and current_user.id != user_id:
            return {"message": "You are not authorized to view these orders"}, HTTPStatus.FORBIDDEN

        user = User.get_by_id(user_id)
        orders = user.order

        return orders, HTTPStatus.OK
        

@order_namespace.route('/status/<int:order_id>')
class UpdateOrderStatus(Resource):

    @order_namespace.expect(order_status_model)
    @order_namespace.marshal_with(order_model)
    @order_namespace.doc(
        description = "Update the order's status given its ID"
    )
    @jwt_required()
    def patch(self,order_id):
        """
            Update an order's status 
        """
        current_user = User.query.filter_by(userName=get_jwt_identity()).first()
        if current_user.role != 'ADMIN':
            return {"message": "Only admins can update order status"}, HTTPStatus.FORBIDDEN

        data = order_namespace.payload

        order_to_update = Order.get_by_id(order_id)
        order_to_update.order_status = data['order_status']
        order_to_update.date_updated = datetime.utcnow()

        db.session.commit()

        return order_to_update, HTTPStatus.OK
    


@order_namespace.route('/resources')
class ResourceManagement(Resource):
    @order_namespace.marshal_list_with(resource_model)
    @order_namespace.doc(description="Get all resources")
    @jwt_required()
    def get(self):
        """
            Get all resources
        """
        current_user = User.query.filter_by(userName=get_jwt_identity()).first()
        if current_user.role != 'ADMIN':
            return {"message": "Only admins can view resources"}, HTTPStatus.FORBIDDEN

        resources = ResourceModel.query.all()
        return resources, HTTPStatus.OK

    @order_namespace.expect(resource_model)
    @order_namespace.marshal_with(resource_model)
    @order_namespace.doc(description="Add a new resource")
    @jwt_required()
    def post(self):
        """
            Add a new resource
        """
        current_user = User.query.filter_by(userName=get_jwt_identity()).first()
        if current_user.role != 'ADMIN':
            return {"message": "Only admins can add resources"}, HTTPStatus.FORBIDDEN

        data = order_namespace.payload

        new_resource = ResourceModel(
            type=data['type'],
            name=data['name'],
            quantity=data['quantity']
        )

        new_resource.save()

        return new_resource, HTTPStatus.CREATED

@order_namespace.route('/resources/<int:resource_id>')
class ResourceUpdate(Resource):
    @order_namespace.expect(resource_model)
    @order_namespace.marshal_with(resource_model)
    @order_namespace.doc(description="Update a resource")
    @jwt_required()
    def put(self, resource_id):
        """
            Update a resource
        """
        current_user = User.query.filter_by(userName=get_jwt_identity()).first()
        if current_user.role != 'ADMIN':
            return {"message": "Only admins can update resources"}, HTTPStatus.FORBIDDEN

        data = order_namespace.payload

        resource_to_update = ResourceModel.get_by_id(resource_id)
        resource_to_update.type = data['type']
        resource_to_update.name = data['name']
        resource_to_update.quantity = data['quantity']

        db.session.commit()

        return resource_to_update, HTTPStatus.OK
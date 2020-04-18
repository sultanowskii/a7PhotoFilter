from flask_restful import reqparse


parser = reqparse.RequestParser()
parser.add_argument('name')
parser.add_argument('users_id')
parser.add_argument('remove_user', type=bool)
from flask_restful import reqparse


parser = reqparse.RequestParser()
parser.add_argument('name')
parser.add_argument('user_id', type=int)
parser.add_argument('remove_user', type=bool)
from flask_restful import reqparse


parser = reqparse.RequestParser()
parser.add_argument('name')
parser.add_argument('lastname')
parser.add_argument('rooms_id', type=int)
parser.add_argument('remove_room', type=bool)

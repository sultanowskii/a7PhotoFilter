from flask_restful import reqparse


parser = reqparse.RequestParser()
parser.add_argument('action')
parser.add_argument('fid', type=int)

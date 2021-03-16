from flask import Blueprint, jsonify, request

main = Blueprint('execute', __name__)

@main.route('/api/run_experiments', methods=['POST'])
def add_movie():
    movie_data = request.get_json()
    print(movie_data)
    return 'Done', 201

@main.route('/api/get_data',methods=['GET'])
def get_data():
    return jsonify({"TEST":"22","TEMP":22})


from flask import Flask, request, jsonify
from __init__ import create_app
import docker
app = create_app()


@app.route('/api/hello')
def hello_world():
    # client = docker.from_env()
    # lefse = client.containers.get("lefse")
    # lefse.start()
    return 'Hello World!'


if __name__ == '__main__':
    app.run()

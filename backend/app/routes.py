from flask import Blueprint, jsonify, send_from_directory
import os

main = Blueprint('main', __name__)

@main.route('/')
def home():
    return send_from_directory('..', 'frontend/index.html')

@main.route('/<path:path>')
def static_files(path):
    return send_from_directory('frontend', path)

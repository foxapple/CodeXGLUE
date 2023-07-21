from flask import Blueprint, jsonify, render_template

from .models import Zip

api = Blueprint('api', __name__)

@api.route('/<zip>')
def query(zip):
    zip = Zip.query.filter_by(zip=zip).first_or_404()

    return jsonify(dict(zip=zip.zip, lat=zip.lat, lng=zip.lng))

@api.after_request
def add_api_header(response):
    response.cache_control.max_age = 31536000
    return response

from flask import Flask, jsonify, request, redirect
from .base import Application
app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def home():
    app_instance = Application()
    if request.method == 'POST':
        data = request.json
        base_url = request.headers.get('Host')
        result = app_instance.encode(
            data['text'],
            expires=data.get('expires'),
            domain=data.get('domain') or "")
        if data.get('domain'):
            return jsonify({"url": f"{base_url}/{result}"})
        return jsonify({'data': 'result'})
    return jsonify({'date': 'Helo world'})


@app.route('/<custom_path>', methods=['GET'])
def redirect_func(custom_path):
    encoded_string = custom_path
    app_instance = Application()
    result = app_instance.decode(encoded_string)
    if result['domain']:
        return redirect(
            app_instance.generate_url(result, path='/edit-resumes/'))

    return jsonify(result)

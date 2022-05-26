import json
# from http.server import BaseHTTPRequestHandler
from base import Application
from flask import Flask, jsonify

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def home():
    return jsonify({'hello': 'world'})


class handler(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def as_json(self, data):
        self.wfile.write(str(json.dumps(data)).encode())
        return

    def redirect(self, url):
        self.send_response(302)
        self.send_header('Content-type', 'text/html')
        self.send_header('Location', url)
        self.end_headers()

    def do_GET(self):
        path = self.path
        if path not in ['/']:
            encoded_string = path[1:]
            app_instance = Application()
            result = app_instance.decode(encoded_string)
            if result['domain']:
                self.redirect(
                    app_instance.generate_url(result, path='/edit-resumes/'))
                return
            else:
                self._set_headers()
                self.as_json(result)
        else:
            self.as_json({'date': 'Helo world'})

    def do_POST(self):
        self.data_string = self.rfile.read(int(self.headers['Content-Length']))
        self._set_headers()
        data = json.loads(self.data_string)
        base_url = self.headers['Host']
        app_instance = Application()
        result = app_instance.encode(
            data['text'],
            expires=data.get('expires'),
            domain=data.get('domain') or "")
        if data.get('domain'):
            self.as_json({"url": f"{base_url}/{result}"})
        else:
            self.as_json({'data': result})

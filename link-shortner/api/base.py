from datetime import datetime
import base64
import csv
from urllib.parse import quote_plus, unquote_plus
import os

BASE_DIR = os.path.dirname(os.path.realpath(__file__))


def encode_text(text, no_behind=7):
    result = [ord(x) + no_behind for x in text]
    transformed = "".join([chr(x) for x in result])
    return base64.urlsafe_b64encode(transformed.encode('utf-8'))


def decode_text(text, no_behind=7):
    decoded = base64.urlsafe_b64decode(text)
    result = [ord(x) - no_behind for x in decoded.decode('utf-8')]
    return "".join([chr(x) for x in result])


def get_domains():
    # result = []
    return [{
        "index": "01",
        "domain": "http://localhost:3000"
    }, {
        "index": "02",
        "domain": "https://staging.careerlyft.com"
    }, {
        "index": "03",
        "domain": "https://app.careerlyft.com"
    }]
    # with open(os.path.join(BASE_DIR, 'domains.csv')) as csv_file:
    #     csv_reader = csv.reader(csv_file, delimiter=",")
    #     line_count = 0
    #     for row in csv_reader:
    #         if line_count == 0:
    #             pass
    #         else:
    #             result.append({'index': row[0], 'domain': row[1]})
    #         line_count += 1
    # return result


class Application(object):
    def encode(self, text, expires=None, domain=""):
        full_text = f"{text}"
        if expires:
            full_text = f"{full_text}-ed:{expires}"
        result = encode_text(full_text).decode('utf-8')
        result += "-d:{}".format(domain)
        return quote_plus(result)

    def decode(self, code):
        without_domain = unquote_plus(code).split("-d:")
        domain = None
        if len(without_domain) > 1:
            domain = without_domain[1] or None
        decoded = decode_text(without_domain[0])
        split_by_salt = decoded
        date_split = split_by_salt.split("-ed:")
        split_by_salt = date_split[0]
        expires = None
        expired = False
        if len(date_split) > 1:
            expires = date_split[1]
            try:
                as_date = datetime.strptime(expires, "%Y-%m-%d")
                expired = datetime.now() > as_date
            except ValueError:
                pass
        if domain:
            instance = [x for x in get_domains() if x['index'] == domain]
            if len(instance) > 0:
                domain = instance[0]['domain']

        result = {
            "text": split_by_salt,
            'expires': expires,
            'expired': expired,
            'domain': domain
        }

        return result

    def generate_url(self, result, path=""):
        if not result['expired'] and result['domain']:
            constructed_string = f"{result['domain']}{path}"
            if result['expires']:
                as_timestamp = datetime.strptime(result['expires'],
                                                 "%Y-%m-%d").timestamp() * 1000
                constructed_string += f"{as_timestamp}/"
            return f"{constructed_string}{result['text']}"
        return ""

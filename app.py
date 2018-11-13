#!/usr/bin/env python3
import boto3
import botocore
import uuid
import urllib.parse
import urllib.request
import json
import os
from flask import Flask
import flask
import flask_limiter
import flask_limiter.util
from jinja2 import Template
from crossdomain import crossdomain
app = Flask(__name__)
limiter = flask_limiter.Limiter(
    app,
    key_func=flask_limiter.util.get_remote_address,
    storage_uri=os.getenv('UPLOAD_RATE_LIMIT_STORAGE', 'memory://'),
    key_prefix="rate_limiter:"
)

S3_UPLOAD_GRACE_PERIOD = 10

def get_s3_current_servicec_provider_envvar(var):
    return os.getenv(f"S3_{os.getenv('S3_CURRENT_SERVICE_PROVIDER')}_{var}")

def is_captcha_enabled():
    return os.getenv('CAPTCHA_ENABLED', 'N').upper() != 'N'

@app.route("/")
def homepage():
    print(flask.request.url_root)
    with open('upload.html') as f:
        template = Template(f.read())
    return template.render(
            fileSizeLimit=get_s3_current_servicec_provider_envvar("MAX_FILE_SIZE"),
            captcha_enabled=is_captcha_enabled(),
            captcha_site_key=os.getenv('CAPTCHA_SITE_KEY', ''),
            upload_rate_limit=os.getenv('UPLOAD_RATE_LIMIT', '')
        )

@app.route("/get_presigned_post", methods=['POST'])
@limiter.limit(os.getenv('UPLOAD_RATE_LIMIT', ''), error_message="Daily upload limit exceeded.\nPlease try again tomorrow.")
def get_presigned_post():
    if is_captcha_enabled():
        print(flask.request.args.get('g-recaptcha-response'))
        request = urllib.request.Request('https://www.google.com/recaptcha/api/siteverify',
            data=urllib.parse.urlencode(
                {'secret': os.getenv('CAPTCHA_SECRET_KEY'), 'response': flask.request.form.get('g-recaptcha-response')}
            ).encode(),
        method='POST')
        response = urllib.request.urlopen(request)
        if not json.loads(response.read().decode('utf-8'))["success"]:
            return flask.Response("INVALID CAPTCHA!", status=401)

    s3 = boto3.client('s3')
    presigned_post = s3.generate_presigned_post(
        Bucket=get_s3_current_servicec_provider_envvar("BUCKET"),
        Key=get_s3_current_servicec_provider_envvar('PREFIX')+str(uuid.uuid4())+get_s3_current_servicec_provider_envvar('SUFFIX'),
        Conditions=[
            {"success_action_redirect": f"{flask.request.url_root}uploaded"}, ["starts-with", "$Content-Type", ""], {"Cache-Control": f"max-age={get_s3_current_servicec_provider_envvar('CACHE_STORAGE_DURATION')}"}, ["content-length-range", 0, int(get_s3_current_servicec_provider_envvar("MAX_FILE_SIZE"))]
        ],
        Fields={"Cache-Control": f"max-age={get_s3_current_servicec_provider_envvar('CACHE_STORAGE_DURATION')}", "success_action_redirect": f"{flask.request.url_root}uploaded"},
        ExpiresIn=S3_UPLOAD_GRACE_PERIOD
    )
    return flask.jsonify(presigned_post)

@app.route("/uploaded", methods=['GET', 'OPTIONS'])
def uploaded():
    if flask.request.method == 'OPTIONS':
        response = flask.Response("")
    else:
        response = flask.Response(f"/view/{os.getenv(f'S3_CURRENT_SERVICE_PROVIDER')}/{urllib.parse.quote(flask.request.args.get('key'))}")
    response.headers['Access-Control-Allow-Origin'] = "*"
    response.headers['Access-Control-Allow-Methods'] = "GET"
    return response

@app.route('/view/<string:service_provider>/<path:filename>')
def result(service_provider, filename):
    with open('result.html') as f:
        template = Template(f.read())
    return template.render(fileName=f"{get_s3_current_servicec_provider_envvar('CLOUDFLARE_ROOT')}/{filename}")

@app.errorhandler(429)
def ratelimit_handler(e):
    return flask.Response(e.description, status=401)

#!/usr/bin/env python3
import boto3
import botocore
import uuid
import urllib
import os
from flask import Flask
import flask
from jinja2 import Template
from crossdomain import crossdomain
app = Flask(__name__)

S3_UPLOAD_GRACE_PERIOD = 10

def get_s3_current_servicec_provider_envvar(var):
    return os.getenv(f"S3_{os.getenv('S3_CURRENT_SERVICE_PROVIDER')}_{var}")

@app.route("/")
def homepage():
    print(flask.request.url_root)
    with open('upload.html') as f:
        template = Template(f.read())
    return template.render(fileSizeLimit=get_s3_current_servicec_provider_envvar("MAX_FILE_SIZE"))

@app.route("/get_presigned_post")
def get_presigned_post():
    s3 = boto3.client('s3')
    presigned_post = s3.generate_presigned_post(
        Bucket=get_s3_current_servicec_provider_envvar("BUCKET"),
        Key=str(uuid.uuid4()),
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
        response = flask.Response(f"/view/{os.getenv(f'S3_CURRENT_SERVICE_PROVIDER')}/{flask.request.args.get('key')}")
    response.headers['Access-Control-Allow-Origin'] = "*"
    response.headers['Access-Control-Allow-Methods'] = "GET"
    return response

@app.route('/view/<string:service_provider>/<string:filename>')
def result(service_provider, filename):
    with open('result.html') as f:
        template = Template(f.read())
    return template.render(fileName=f"{get_s3_current_servicec_provider_envvar('CLOUDFLARE_ROOT')}/{filename}")

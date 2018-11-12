#!/usr/bin/env python3
import boto3
import botocore
import uuid
import urllib
import os
from flask import Flask
import flask
from jinja2 import Template
app = Flask(__name__)

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
            {"acl": "public-read"}, {"success_action_redirect": f"{flask.request.url_root}uploaded"}, ["starts-with", "$Content-Type", ""], ["content-length-range", 0, int(get_s3_current_servicec_provider_envvar("MAX_FILE_SIZE"))]
        ],
        Fields={"acl": "public-read", "success_action_redirect": f"{flask.request.url_root}uploaded"},
        ExpiresIn=30
    )
    return flask.jsonify(presigned_post)

@app.route("/uploaded")
def uploaded():
    return flask.redirect(f"/view/{os.getenv(f'S3_CURRENT_SERVICE_PROVIDER')}/{flask.request.args.get('key')}", code=302)

@app.route('/view/<string:service_provider>/<string:filename>')
def result(service_provider, filename):
    with open('result.html') as f:
        template = Template(f.read())
    return template.render(fileName=f"{get_s3_current_servicec_provider_envvar('URL_ROOT')}/{urllib.parse.quote(filename)}")

#!/usr/bin/env python3
import boto3
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
def upload():
    print(flask.request.url_root)
    with open('upload.html') as f:
        template = Template(f.read())
    s3 = boto3.client('s3')
    post = s3.generate_presigned_post(
        Bucket=get_s3_current_servicec_provider_envvar("BUCKET"),
        Key=str(uuid.uuid4())+'_${filename}',
        Conditions=[
            {"acl": "public-read"}, {"success_action_redirect": f"{flask.request.url_root}uploaded"}, ["starts-with", "$Content-Type", ""], ["content-length-range", 0, int(get_s3_current_servicec_provider_envvar("MAX_FILE_SIZE"))]
        ],
        Fields={"acl": "public-read", "success_action_redirect": f"{flask.request.url_root}uploaded", "Content-Type": "binary/octet-stream"}
    )
    return template.render(post=post, fileSizeLimit=get_s3_current_servicec_provider_envvar("MAX_FILE_SIZE"))

@app.route("/uploaded")
def uploaded():
    #TODO: secure it. Only accept redirections originating from Amazon
    return flask.redirect(f"/view/{os.getenv(f'S3_CURRENT_SERVICE_PROVIDER')}/{urllib.parse.quote(flask.request.args.get('key'))}", code=302)

@app.route('/view/<string:service_provider>/<string:filename>')
def result(service_provider, filename):
    with open('result.html') as f:
        template = Template(f.read())
    return template.render(fileName=f"{get_s3_current_servicec_provider_envvar('URL_ROOT')}/{urllib.parse.quote(filename)}")

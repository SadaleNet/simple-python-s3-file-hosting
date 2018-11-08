#!/usr/bin/env python3
import boto3
import uuid
import urllib
import os
from flask import Flask
import flask
from jinja2 import Template
app = Flask(__name__)

@app.route("/")
def upload():
    print(flask.request.url_root)
    with open('upload.html') as f:
        template = Template(f.read())
    s3 = boto3.client('s3')
    post = s3.generate_presigned_post(
        Bucket=os.getenv('AWS_BUCKET'),
        Key=str(uuid.uuid4())+'/${filename}',
        Conditions=[
            {"acl": "public-read"}, {"success_action_redirect": f"{flask.request.url_root}uploaded"}, ["starts-with", "$Content-Type", ""], ["content-length-range", 0, int(os.getenv('AWS_MAX_FILE_SIZE'))]
        ],
        Fields={"acl": "public-read", "success_action_redirect": f"{flask.request.url_root}uploaded", "Content-Type": "image/png"}
    )
    return template.render(post=post)

@app.route("/uploaded")
def uploaded():
    #TODO: secure it. Only accept redirections originating from Amazon
    return flask.redirect(urllib.parse.quote(flask.request.args.get('key', '/')), code=302)

@app.route('/<path:filename>')
def result(filename):
    with open('result.html') as f:
        template = Template(f.read())
    return template.render(fileName=f"{os.getenv('AWS_URL_ROOT')}/{urllib.parse.quote(filename)}")

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
def upload():
    print(flask.request.url_root)
    with open('upload.html') as f:
        template = Template(f.read())
    s3 = boto3.client('s3')
    post = s3.generate_presigned_post(
        Bucket=get_s3_current_servicec_provider_envvar("BUCKET"),
        Key='upload_'+str(uuid.uuid4()),
        Conditions=[
            {"success_action_redirect": f"{flask.request.url_root}uploaded"}, ["starts-with", "$Content-Type", ""], ["content-length-range", 0, int(get_s3_current_servicec_provider_envvar("MAX_FILE_SIZE"))]
        ],
        Fields={"success_action_redirect": f"{flask.request.url_root}uploaded", "Content-Type": "binary/octet-stream"}
    )
    return template.render(post=post, fileSizeLimit=get_s3_current_servicec_provider_envvar("MAX_FILE_SIZE"))

@app.route("/uploaded")
def uploaded():
    s3 = boto3.client('s3')
    filename_suffix = flask.request.args.get('key').split('_',1)[1]
    destination_path = f"view_{filename_suffix}"
    try:
        s3.head_object(
            Bucket=get_s3_current_servicec_provider_envvar("BUCKET"),
            Key=destination_path
        )
    except botocore.exceptions.ClientError as e:
        print('NOT FOUND!')
        if e.response['Error']['Code'] == '404':
            s3.copy_object(
                Bucket=get_s3_current_servicec_provider_envvar("BUCKET"),
                CopySource=f"{get_s3_current_servicec_provider_envvar('BUCKET')}/{flask.request.args.get('key')}",
                Key=destination_path,
                ACL="public-read"
            )
    s3.delete_object(
        Bucket=get_s3_current_servicec_provider_envvar("BUCKET"),
        Key=flask.request.args.get('key')
    )
    return flask.redirect(f"/view/{os.getenv(f'S3_CURRENT_SERVICE_PROVIDER')}/{filename_suffix}", code=302)

@app.route('/view/<string:service_provider>/<string:filename>')
def result(service_provider, filename):
    with open('result.html') as f:
        template = Template(f.read())
    return template.render(fileName=f"{get_s3_current_servicec_provider_envvar('URL_ROOT')}/view_{urllib.parse.quote(filename)}")

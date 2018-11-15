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
app = Flask(__name__)
limiter = flask_limiter.Limiter(
    app,
    key_func=flask_limiter.util.get_remote_address,
    storage_uri=os.getenv('UPLOAD_RATE_LIMIT_STORAGE', 'memory://'),
    key_prefix="rate_limiter:"
)

S3_UPLOAD_GRACE_PERIOD = 10

def get_s3_current_servicec_provider_envvar(var, default=''):
    return os.getenv(f"S3_{os.getenv('S3_CURRENT_SERVICE_PROVIDER')}_{var}", default)

def is_env_enabled(env_value):
    return env_value.upper() != 'N'

def is_captcha_enabled():
    return is_env_enabled(os.getenv('CAPTCHA_ENABLED', 'N'))

def humanBytesToValue(humanReadableBytes):
    units = {"B": 1, "KB": 10**3, "MB": 10**6, "GB": 10**9, "TB": 10**12,
                "KIB": 2**10, "MIB": 2**20, "GIB": 2**30, "TIB": 2**40}
    number, unit = [string.upper().strip() for string in humanReadableBytes.split()]
    return int(float(number)*units[unit])

@app.route("/")
def homepage():
    print(flask.request.url_root)
    with open('upload.html') as f:
        template = Template(f.read())
    return template.render(
            service_name=os.getenv('SERVICE_NAME', 'S3 Temporary File Upload'),
            file_size_limit_human=get_s3_current_servicec_provider_envvar("MAX_FILE_SIZE"),
            file_size_limit=humanBytesToValue(get_s3_current_servicec_provider_envvar("MAX_FILE_SIZE")),
            captcha_enabled=is_captcha_enabled(),
            captcha_site_key=os.getenv('CAPTCHA_SITE_KEY', ''),
            upload_rate_limit=os.getenv('UPLOAD_RATE_LIMIT', '')
        )

@app.route("/get_presigned_post", methods=['POST'])
@limiter.limit(os.getenv('UPLOAD_RATE_LIMIT', ''), error_message="Daily upload limit exceeded.\nPlease try again tomorrow.")
def get_presigned_post():
    if is_captcha_enabled():
        request = urllib.request.Request('https://www.google.com/recaptcha/api/siteverify',
            data=urllib.parse.urlencode(
                {'secret': os.getenv('CAPTCHA_SECRET_KEY'), 'response': flask.request.form.get('g-recaptcha-response')}
            ).encode(),
        method='POST')
        response = urllib.request.urlopen(request)
        if not json.loads(response.read().decode('utf-8'))["success"]:
            return flask.Response("Invalid Captcha", status=401)

    filename = flask.request.form.get('filename')
    if '/' in filename or '\\' in filename:
        return flask.Response("Invalid Filename", status=400)

    file_extension = os.path.splitext(filename)[1]
    cloudflare_suffix = ''
    static_content_file_extensions = ['.bmp', '.css', '.csv', '.doc', '.docx', '.ejs', '.eot', '.eps', '.gif', '.ico', '.jar', '.jpeg', '.jpg', '.js', '.mid', '.midi', '.otf', '.pdf', '.pict', '.pls', '.png', '.ppt', '.pptx', '.ps', '.svg', '.svgz', '.swf', '.tif', '.tiff', '.ttf, class', '.webp', '.woff', '.woff2', '.xls', '.xlsx'] #See https://support.cloudflare.com/hc/en-us/articles/200172516-Which-file-extensions-does-Cloudflare-cache-for-static-content-

	#If the file extension isn't the static one, append the default file extension to the filename
    if sum([filename.endswith(i) for i in static_content_file_extensions]) == 0:
        cloudflare_suffix = get_s3_current_servicec_provider_envvar('CLOUDFLARE_DEFAULT_FILE_EXTENSION')

    s3 = boto3.client('s3',
        aws_access_key_id=get_s3_current_servicec_provider_envvar('ACCESS_KEY_ID'),
        aws_secret_access_key=get_s3_current_servicec_provider_envvar('SECRET_ACCESS_KEY')
    )
    presigned_post = s3.generate_presigned_post(
        Bucket=get_s3_current_servicec_provider_envvar("BUCKET"),
        Key=get_s3_current_servicec_provider_envvar('FILENAME').format(uuid=uuid.uuid4(), filename=filename, file_extension=file_extension, cloudflare_suffix=cloudflare_suffix),
        Conditions=[
            {"success_action_redirect": f"{flask.request.url_root}uploaded"}, ["starts-with", "$Content-Type", ""], {"Cache-Control": f"max-age={get_s3_current_servicec_provider_envvar('CACHE_STORAGE_DURATION')}"}, ["content-length-range", 0, humanBytesToValue(get_s3_current_servicec_provider_envvar("MAX_FILE_SIZE"))]
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
    #Remove the quotes to eliminate security risk
    #Due to the handling of quote escape is different between HTML and Javascript, there's no easy way to come up with
    #a universal way to handle quote escape. So we just remove them instead of escaping them
    filename = filename.replace('"', '').replace("'", "")
    return template.render(
            service_name=os.getenv('SERVICE_NAME', 'S3 Temporary File Upload'),
            fileName=f"{get_s3_current_servicec_provider_envvar('CLOUDFLARE_ROOT')}/{filename}"
    )

@app.route('/robots.txt')
def robots_txt():
    return "User-agent: *\nDisallow: /view/\nDisallow: /uploaded"

@app.errorhandler(429)
def ratelimit_handler(e):
    return flask.Response(e.description, status=401)

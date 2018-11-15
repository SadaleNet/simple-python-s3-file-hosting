#This script runs the Python S3 Simple File Hosting instance without using Docker
#You have to set the environment variables below before running this script

#The name of the AWS bucket
export S3_AWS_BUCKET="<your-bucket-name-goes-here>"
#Used for telling between AWS or Google Cloud Storage or Azure or Digital Ocean or whatever
export S3_AWS_BACKEND_TYPE="AWS_S3"
export S3_AWS_URL_ROOT="https://s3.amazonaws.com/<your-bucket-name-goes-here>"
#Set S3_AWS_CLOUDFLARE_ROOT to the same value as S3_AWS_URL_ROOT if Cloudflare isn't used
export S3_AWS_CLOUDFLARE_ROOT="https://<your-cloudflare-caching-domain-name-goes-here>"
#Object names in the bucket. Available variables: uuid, file_extension, filename, cloudflare_suffix
#uuid - the UUID of the file. Generated by the time on upload
#file_extension - the file extension of the file. It does not necessarily match the MIME type of the file
#filename - the filename, including the file extension
#cloudflare_suffix - S3_*_CLOUDFLARE_DEFAULT_FILE_EXTENSION if the file is not "static content", empty string else. This is used for making Cloudflare to treat the uploaded file as static content. Cloudflare only supports ignoring query string for static content.
#    See https://support.cloudflare.com/hc/en-us/articles/200172516
export S3_AWS_FILENAME="uploads/{uuid}{file_extension}"
export S3_AWS_CLOUDFLARE_DEFAULT_FILE_EXTENSION=".pls"
#Maximum file size. The unit must be separated by space. Unit can be B, kB, MB, GB, TB, KiB, MiB, GiB or TiB. Case insensitive.
export S3_AWS_MAX_FILE_SIZE="100 MiB"
#The x in "Cache-Control: max-age=x" header. This is sent to AWS when obtaining the presigned POST. It affects browser cache, or Cloudflare cache.
export S3_AWS_CACHE_STORAGE_DURATION="86400"
#AWS credentials.
export S3_AWS_ACCESS_KEY_ID="<your-aws-access-key-id-goes-here>"
export S3_AWS_SECRET_ACCESS_KEY="<your-aws-secret-access-key-goes-here>"
#The service provider. The * of S3_*_BUCKET, S3_*_BACKEND_TYPE, etc.
export S3_CURRENT_SERVICE_PROVIDER="AWS"
#Choose if enable Recaptcha v2 invisible. Anything not "N" or "n" means yes.
export CAPTCHA_ENABLED="N"
#Credntials of Recaptcha
export CAPTCHA_SITE_KEY="<your-recaptcha-site-key-goes-here>"
export CAPTCHA_SECRET_KEY="<your-recaptcha-secret-key-goes-here>"
#Upload limit. Set it to "" or remove this line to disable upload limit. See the documentation of flask-limiter.
export UPLOAD_RATE_LIMIT="10 per day"
#Database for storing the upload limit. See the documentation of flask-limiter.
export UPLOAD_RATE_LIMIT_STORAGE="memory://"
#The name of the server instance
export SERVICE_NAME="Simple Python S3 File Hosting"

FLASK_APP=./app/app.py flask run -h 0.0.0.0 -p 5000

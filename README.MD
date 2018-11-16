# Simple Python S3 File Hosting

An implementation of a simple file hosting website using S3 object storage.

Live demo: [https://stfu.top](https://stfu.top) (Simple Temporary File Upload)

(Remarks: This demo uses AWS S3's lifecycle management to automatically delete the hosted files after a day. The file deletion feature is not implemented in the website itself)

# Features

* Highly scalable by using AWS S3 object storage
* Drag and drop file upload
* File preview for image, video, audio, pdf, text and sandboxed HTML
* Configurable Recaptcha (v2 Invisible) support
* Configurable rate limiting per IP address
* Almost stateless, with the stateful part only for performing rate-limit per IP address, which can be disabled

# Dependencies

* Flask
* Flask-limiter
* Boto3
* Redis (optional, for Flask-limiter. RAM can alternatively be used as a replacement)

# Running the Website

**WARNING**: Be-sure to read the section DoS Countermeasurements or you may get DoS'd and get excessively billed by AWS S3

* Running without Docker: install the dependencies. Then modify the environment variables in [run-example.sh](./run-example.sh) and run it
* Running with Docker: `docker run -e S3_AWS_BUCKET="foobar.example.com" -e S3_AWS_BACKEND_TYPE="AWS_S3" -e ...<put all of your other configuration environment variables here>... sadalenet/python_s3_file_upload:latest`
* Running with Docker Compose/Swarm: Modify docker-compose-example.yml, then run `docker stack deploy -c docker-compose-example.yml`

# Configuration

The configuration is loaded from environment variables as documented below:

<pre>
S3_CURRENT_SERVICE_PROVIDER: The current backend used. Example: "AWS". It is the value of "*" in "S3_*_BUCKET", "S3_*_BACKEND_TYPE", etc. This environment variable makes switching backend storage provider easy.
S3_*_BUCKET: Bucket name of S3. Example: "foobar.example.com"
S3_*_BACKEND_TYPE: Used for telling between AWS or Google Cloud Storage or Azure or Digital Ocean or whatever. Currently the only valid value is "AWS_S3"
S3_*_URL_ROOT: URL to AWS bucket. Example: "https://s3.amazonaws.com/foobar.example.com"
S3_*_CLOUDFLARE_ROOT: URL to Cloudflare. Set it to the same value as S3_*_URL_ROOT if Cloudflare isn't used. Example: "https://s3cloudflarecache.foobar.example.com"
S3_*_FILENAME: The file name of the uploaded file to be stored in S3. Example: "uploads/{uuid}{file_extension}{cloudflare_suffix}". Available variables: uuid, file_extension, filename, cloudflare_suffix
	uuid - the UUID of the file. Generated at the time of the beginning of file upload
	file_extension - the file extension of the file. It does not necessarily match the MIME type of the file
	filename - the filename, including the file extension
	cloudflare_suffix - S3_*_CLOUDFLARE_DEFAULT_FILE_EXTENSION if the file is not "static content", empty string else. This is used for making Cloudflare to treat the uploaded file as static content. Cloudflare only supports ignoring query string for static content.
S3_*_CLOUDFLARE_DEFAULT_FILE_EXTENSION: The value of {cloudflare_suffix} for S3_*_FILENAME if file extension of the uploaded file is not "static content" as defined by Cloudflare
S3_*_MAX_FILE_SIZE: Maximum file size. The unit must be separated by space. Unit can be B, kB, MB, GB, TB, KiB, MiB, GiB or TiB. Case insensitive. Example: "100 MiB"
S3_*_CACHE_STORAGE_DURATION: The x in "Cache-Control: max-age=x" header. This is sent to AWS when obtaining the presigned POST. It affects browser cache, or Cloudflare cache. Example: "86400"
S3_*_ACCESS_KEY_ID: Your AWS access key ID
S3_*_SECRET_ACCESS_KEY: Your AWS secret access key
CAPTCHA_ENABLED: Enables "Recaptcha v2 Invisible". Anything not "N" or "n" means yes. Example: "Y"
CAPTCHA_SITE_KEY: Your "Recaptcha v2 Invisible" site key
CAPTCHA_SECRET_KEY: Your "Recaptcha v2 Invisible" secret key
UPLOAD_RATE_LIMIT: The max number of files can be uploaded by the user per a period of time. Not setting it or setting it to empty string would eliminate the limit. See the documentation of flask-limiter. Example: "10 per day"
UPLOAD_RATE_LIMIT_STORAGE: Database for storing the upload limit. See the documentation of flask-limiter. Example: "memory://", "redis://localhost:6379"
REVERSE_PROXY_FIX: Set this to "Y" if you're using a reverse proxy. See http://flask.pocoo.org/docs/0.12/deploying/wsgi-standalone/#proxy-setups. Setting it to "Y" without using the reverse proxy would render the upload limit useless because the attackers would be able to spoof their IP address.
SERVICE_NAME: Name of the server instance to be displayed on the website. Example: "Simple Python S3 File Hosting"
HOSTER_NAME: Name of the hoster to be displayed on the website. Example: "John Smith"
BACKEND_NAME: Backend name shown on the website. Users have to comply with their terms of service for uploading the files. Example: "AWS S3"
CONTACT_EMAIL: The contact email in case of abuse. Example: "foobar@example.com"
UPLOAD_REMARKS: Remarks shown on the upload page. Example: "Storage duration: 1 day"
RESULT_REMARKS: Remarks shown on the view file page. Example: "All uploaded files will be removed after a day."
</pre>


# DoS Countermeasurements

Since this file hosting is using S3 object storage as its back-end, it is vulnerable to DoS attacks that will incur a lot of cost to the hoster. Here's what is billed by AWS S3:

* Storage space
* HTTP requests to the S3 storage
* Data Transfer (from S3 to Internet)

The following countermeasurements had been taken for the live demo of the website:

1. Set a maximum file size for each file. It limits the storage space used for each file.
2. Set a file upload limit per a period of time. It limits the rate of expansion of storage space used. It also limits the amount of HTTP POST requests generated.
3. Use AWS S3 lifecycle management to delete old files. It limits the total storage space used.
4. Configure Recaptcha. It prevents bots from uploading files.
5. Use Cloudflare or any other CDN to cache the content of AWS S3. It makes the CDN to download the stored files from AWS S3 once and cache it for a while. It greatly reduces the amount of HTTP GET requests made to AWS S3, as well as the data transfer from S3 to internet.
6. Configure Cloudflare so that it ignores query string of requests sent to AWS S3. That's because if query string isn't ignored, the attacker could keep making requests with random query string to bypass the Cloudflare cache. That would enable the attacker keep generating HTTP GET requests to S3, and keep getting AWS S3 to send data to the internet.
	* For Cloudflare, this countermeasurement only works for ["static content"](https://support.cloudflare.com/hc/en-us/articles/200172516-Which-file-extensions-does-Cloudflare-cache-for-static-content-), which is files with certain filename extensions defined by Cloudflare. For the files uploaded with other filename extensions, we have {cloudflare_suffix} for the environment variable `S3_*_FILENAME` for appending an extra file extensions to make Cloudflare to treat the file as "static content".

These countermeasurements are no way being perfect. But this is all what I can come up with for now. If you have more ideas of the countermeasurements, feel free to bring that up by creating an issue or contacting me directly! :)

# Unimplemented Features

* Unit tests
* Support for other S3-compatible storages
* Support for other storage backends

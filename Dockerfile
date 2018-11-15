# Use an official Python runtime as a parent image
FROM python:3.7-alpine

# Set the working directory to /app
WORKDIR /app

# Copy the pip requirements into /tmp inside the container
COPY requirements.txt /tmp

# Install any required packages
RUN pip install --trusted-host pypi.python.org -r /tmp/requirements.txt

# Copy the data
COPY app .

# Make port 80 available to the world outside this container
EXPOSE 80

# Used for docker to detect if the container is healthy
HEALTHCHECK --timeout=5s CMD wget -O /dev/null http://localhost || exit 1

# Run app.py when the container launches
CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:80", "app:app"]

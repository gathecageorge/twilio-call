# Use the official Python base image
FROM python:3.8.3-slim-buster

ARG APP_VERSION
ENV APP_VERSION=${APP_VERSION}

# Set the working directory inside the container
WORKDIR /src

# Copy your application files into the container
COPY requirements.txt /src

# Install dependencies (from requirements.txt)
RUN pip install -r /src/requirements.txt

# Specify the command to run your Python app
CMD ["python", "app.py"]

# Use an official Python runtime as a parent image
FROM python:3.12.4-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the port the app runs on (if applicable)
EXPOSE 8000

# Define environment variables (if needed)
ENV PYTHONUNBUFFERED=1

# Command to run the application
CMD ["gunicorn", "wsgi:app", "-c", "gunicorn_conf.py"]
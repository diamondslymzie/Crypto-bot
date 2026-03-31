# Use a super light, clean version of Python
FROM python:3.10-slim

# Set the working directory inside the server
WORKDIR /app

# Copy just the requirements file first to build the environment
COPY requirements.txt .

# Install your Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your files over
COPY . .

# Expose the port Railway uses
EXPOSE 5000

# Tell Gunicorn to run your app and bind it to the proper port
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]

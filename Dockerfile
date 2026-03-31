# Use a fast, official, pre-built Python environment
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install the libraries
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your bot's files into the container
COPY . .

# Expose the port Railway uses
EXPOSE 8080

# Command to turn on the bot
CMD ["python", "bot.py"]

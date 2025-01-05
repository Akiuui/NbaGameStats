FROM python:3.9-slim

# Install required packages
RUN apt update && apt install -y python3-pip && apt clean && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies
COPY requirements.txt /app/
RUN pip3 install -r /app/requirements.txt

# Set the working directory
WORKDIR /app

# Copy all application files
COPY . .

# Run the Flask application
CMD ["waitress-serve", "--port=5000", "app:app"]

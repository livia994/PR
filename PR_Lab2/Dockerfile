FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install system dependencies required for cryptography
RUN apt-get update && \
    apt-get install -y gcc libssl-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install pymysql cryptography

# Expose the ports for Flask (5000) and SocketIO (5001)
EXPOSE 5000 5001

# Set environment variables for Flask
ENV FLASK_APP=app.py
ENV FLASK_ENV=development

# Run the Flask server with SocketIO
CMD ["python", "app.py"]

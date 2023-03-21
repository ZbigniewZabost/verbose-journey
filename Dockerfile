# Use an official Python runtime as a parent image
FROM python:3

# Set the working directory to /app
WORKDIR /app

VOLUME [ "/data" ]

# Install any needed packages specified in requirements.txt
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Download and install the Firefox driver
RUN apt-get update && apt-get install -y --no-install-recommends wget firefox-esr && \
    wget -O /tmp/geckodriver.tar.gz https://github.com/mozilla/geckodriver/releases/download/v0.32.2/geckodriver-v0.32.2-linux64.tar.gz && \
    tar -C /usr/local/bin/ -xzf /tmp/geckodriver.tar.gz && \
    chmod +x /usr/local/bin/geckodriver && \
    rm /tmp/geckodriver.tar.gz && \
    apt-get remove -y wget && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# Copy the rest of the application code into the container
COPY . /app/

# Set the default command to run when the container starts
CMD ["python", "main.py"]

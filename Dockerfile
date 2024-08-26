
FROM python:3.9-slim
WORKDIR /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 3000 available to the world outside this container
EXPOSE 3000

# Define environment variable
ENV NAME Leyline

# Run app.py when the container launches
CMD ["python", "app.py"]


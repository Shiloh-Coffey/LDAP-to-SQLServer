FROM python:3.8

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the Python scripts into the container
COPY main-pull.py .
COPY refresh-pull.py .

# Install any necessary dependencies
RUN pip install ldap3 pyodbc

# Run the script
CMD ["python", "./main-pull.py"]
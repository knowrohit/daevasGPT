# Use an official Python runtime as a parent image
FROM python:3.8

# Set the working directory to /Bernard
WORKDIR /Bernard

# Copy the necessary folders and files into the container at /Bernard
COPY configs/ /Bernard/configs/
COPY models/ /Bernard/models/
COPY static/ /Bernard/static/
COPY templates/ /Bernard/templates/
COPY tokenizers/ /Bernard/tokenizers/
COPY app.py /Bernard/
COPY daevasAGI.py /Bernard/
COPY requirements.txt /Bernard/

# Install any needed packages specified in requirements.txt
RUN pip3 install torch -f https://download.pytorch.org/whl/cpu/torch_stable.html
RUN pip3 install transformers

RUN pip3 install -r requirements.txt
# Make port 80 available to the world outside this container
EXPOSE 80

# Define environment variable
ENV NAME Bernard

# Run app.py when the container launches
CMD ["python", "app.py"]


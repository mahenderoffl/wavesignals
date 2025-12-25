# Use a newer Python image to support Google AI SDK
FROM python:3.11

# Set the working directory to /code
WORKDIR /code

# Copy the requirements file
COPY ./requirements.txt /code/requirements.txt

# Upgrade pip first (Critical for finding new packages)
RUN pip install --no-cache-dir --upgrade pip

# Install the dependencies
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy the rest of the code
COPY . /code

# Create a non-root user (Security Best Practice for HF)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Expose port 7860 (Hugging Face default)
EXPOSE 7860

# Start the application using Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:7860", "app:app"]

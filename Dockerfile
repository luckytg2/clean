FROM python:3.10-slim

# Install dependencies
RUN pip install --upgrade pip

# Set workdir
WORKDIR /app

# Copy files
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY cleaner_bot.py .

# Run the bot
CMD ["python", "cleaner_bot.py"]

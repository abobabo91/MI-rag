FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create a dummy secrets file to suppress Streamlit warnings
RUN mkdir -p .streamlit && echo "" > .streamlit/secrets.toml

# Expose the port Streamlit runs on
EXPOSE 8080

# Configure Streamlit
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_PORT=8080

CMD ["streamlit", "run", "app.py"]

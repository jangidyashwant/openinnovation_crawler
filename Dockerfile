FROM python:3.9-slim

WORKDIR /usr/src/app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && \
    apt-get install -y wget unzip curl && \
    apt-get install -y xvfb gnupg2 && \
    curl -sSL https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' && \
    apt-get update && apt-get -y install google-chrome-stable && \
    wget https://storage.googleapis.com/chrome-for-testing-public/128.0.6613.137/mac-arm64/chromedriver-mac-arm64.zip && \
    unzip chromedriver_linux64.zip && \
    mv chromedriver /usr/local/bin/ && \
    rm chromedriver_linux64.zip && \
    chmod +x /usr/local/bin/chromedriver

EXPOSE 8080

CMD ["python", "./crawler.py"]

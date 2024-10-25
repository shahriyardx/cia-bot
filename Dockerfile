FROM python:3.12.4-slim

WORKDIR /app

# Install packages
RUN apt-get update -y
RUN apt-get install -y gcc git build-essential libtool automake

COPY requirements.txt ./

RUN pip install -r requirements.txt

COPY . .

CMD [ "sh", "-c", "python3 -O -u main.py" ]
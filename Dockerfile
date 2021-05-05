FROM python:3.8-alpine

WORKDIR /home/chat

RUN apk update && apk add bash

COPY requirements.txt requirements.txt
RUN python -m venv venv
RUN /bin/bash -c "source venv/bin/activate venv"
RUN pip install -r requirements.txt

COPY app app
COPY migrations migrations
COPY app.py config.py ./

ENV FLASK_APP app.py

EXPOSE 5000
ENTRYPOINT ["python", "-m", "flask", "run"]
FROM python:3

RUN  apt-get update; apt-get install -y supervisor

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY flask_receiver.py ./
COPY build-assets/supervisord.conf /etc/supervisor/supervisord.conf


EXPOSE 80

CMD ["supervisord", "-c", "/etc/supervisor/supervisord.conf", "--nodaemon"]

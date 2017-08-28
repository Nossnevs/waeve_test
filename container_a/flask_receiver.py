import os
import signal
from time import sleep

import sys
from flask import Flask
from flask import request
app = Flask(__name__)


@app.route("/")
def hello():
    return str(os.environ['SERVICE_NAME'])


def handler(signum, frame):
    sleep(4)
    sys.exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGTERM, handler)
    app.run(host='0.0.0.0', port=80, processes=2)

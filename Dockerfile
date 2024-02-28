FROM python:3.10-slim-buster

WORKDIR /usr/src/app

COPY . ./

RUN pip3 install --no-cache-dir -r requirements.txt

CMD ["python", "./api.py"]
FROM python:3
RUN mkdir /code /code/app
WORKDIR /code/
ADD requirements.txt /code/
RUN pip install -r requirements.txt
ADD . /code/

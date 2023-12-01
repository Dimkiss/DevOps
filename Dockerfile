FROM python:3.12.0

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["flask", "--app", "main.py", "run"]

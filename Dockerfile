FROM python:3.12

WORKDIR /myapp

COPY requirements.txt .

COPY . .

CMD ["python", "run.py"]
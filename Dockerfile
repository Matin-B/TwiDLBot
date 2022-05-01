FROM python:3.9

COPY app .

RUN python3 -m pip install --upgrade pip
RUN pip3 install -r requirements.txt

ENTRYPOINT ["python3"]

CMD ["main.py"]

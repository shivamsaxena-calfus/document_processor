#
FROM python:3.9

#
WORKDIR /document_processor

#
COPY ./requirements.txt /document_processor/requirements.txt

#
RUN pip install --no-cache-dir --upgrade -r /document_processor/requirements.txt

#
COPY ./app /document_processor/app

#
CMD ["fastapi", "run", "app/main.py", "--port", "5001"]
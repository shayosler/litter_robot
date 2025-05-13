FROM python:3.10-slim

# Disable buffering of stderr and stdout
ENV PYTHONBUFFERED=True
ENV DOCKER_IMAGE=True

WORKDIR /app

COPY ./update_weight_history.py ./
COPY ./requirements.txt ./

RUN pip install -r requirements.txt

CMD ["python3", "update_weight_history.py"]

FROM python:3.8-slim-buster
LABEL project.name=LabEx \
      project.id=Lab03 \
      project.authorA=isabelaedilene \
      project.authorB=Zuquim \
      project.version=0.1.0
ENV TZ America/Sao_Paulo
WORKDIR /opt
COPY . ./
RUN apt-get update; apt-get install -y --no-install-recommends git && \
    pip install --no-cache-dir -r requirements.txt
ENTRYPOINT ["python3", "app.py"]

FROM python:3.7-slim-buster
LABEL project.name=LabEx \
      project.authorA=isabelaedilene \
      project.authorB=Zuquim \
      project.version=1.0.0
ENV TZ America/Sao_Paulo
WORKDIR /opt
COPY . ./
RUN pip install --no-cache-dir -r requirements.txt
ENTRYPOINT ["python3", "app.py"]

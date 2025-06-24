FROM python:3
COPY . .
WORKDIR backend
RUN pip install -r requirements.txt
WORKDIR ..
ENTRYPOINT run_app.sh
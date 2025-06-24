FROM python:3.12
WORKDIR /app
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY . .
RUN chmod +x run_app.sh
ENTRYPOINT ["./run_app.sh"]

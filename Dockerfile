FROM python:3.10
WORKDIR /app
COPY . .
RUN pip install flask pyTelegramBotAPI
EXPOSE 10000
CMD ["python", "app.py"]

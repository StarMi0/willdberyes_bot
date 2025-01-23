FROM ubuntu:latest
LABEL authors="stars"

ENTRYPOINT ["top", "-b"]

# Используем официальный образ Python 3.9
FROM python:3.10

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем зависимости в контейнер
COPY req.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r req.txt

# Копируем весь код в контейнер
COPY . .

# Указываем команду для запуска бота
CMD ["python", "main.py"]

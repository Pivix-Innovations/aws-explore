# syntax=docker/dockerfile:1

FROM node:20-alpine AS frontend
WORKDIR /app

COPY theme/static_src/package.json theme/static_src/package-lock.json ./theme/static_src/
RUN npm --prefix ./theme/static_src ci

# Tailwind @source paths scan project templates/python files, so copy app source too.
COPY aws_explore ./aws_explore
COPY core ./core
COPY scanner ./scanner
COPY theme ./theme
COPY web ./web

RUN npm --prefix ./theme/static_src run build


FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./
COPY --from=frontend /app/theme/static/css/dist /app/theme/static/css/dist

EXPOSE 8000

CMD ["sh", "-c", "until python manage.py migrate; do echo 'Database unavailable, retrying in 2s...'; sleep 2; done && python manage.py collectstatic --noinput && gunicorn aws_explore.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120"]

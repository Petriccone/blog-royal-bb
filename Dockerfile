# Railway: container com Python + Git para o cron poder fazer push dos posts.
FROM python:3.11-slim

# Git é necessário para a Etapa 3 (push para GitHub)
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Mantém o container ativo; o cron chama python -m execution.run_all
CMD ["tail", "-f", "/dev/null"]

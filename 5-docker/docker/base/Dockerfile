
# instalujeny obraz bazowy z pythonem i uv
FROM astral/uv:python3.11-trixie

# zmienne środowiskowe (konfiguracja)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# katalog roboczy w każdym z kontenerów
WORKDIR /app

# definiujemy argument builda
ARG SERVICE_DIR

# kopiuje plik zależności pythona do katalogu roboczego
COPY ./pyproject.toml ./pyproject.toml

# instaluje zależności z pyproject.toml
RUN uv sync

# kopiuje kod serwisu do katalogu roboczego
COPY ${SERVICE_DIR}/ ./

#aplikacja działa na porcie 8000
EXPOSE 8000

# uruchamiamy aplikację
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

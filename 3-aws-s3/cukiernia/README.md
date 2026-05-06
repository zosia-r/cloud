# System Obsługi Zamówień Cukierniczych v2 🎂

## Co nowego względem v1

### 1. Integracja z Amazon S3 (DesignService)
- Pliki graficzne są zapisywane w S3 zamiast lokalnie
- W bazie zapisywane są metadane: nazwa, rozszerzenie, rozmiar, data, klucz S3
- Nowy endpoint `GET /designs/{design_id}/download` — zwraca presigned URL (ważny 1h)

### 2. CQS (Command Query Separation)
Każda operacja to albo Command (zapis) albo Query (odczyt):
- **Command** — modyfikuje stan, np. `CreateOrderCommand`, `ProcessPaymentCommand`
- **Query** — odczytuje stan, np. `GetOrderQuery`, `ListOrdersQuery`

### 3. Mediator
Pośrednik między API a handlerami:
```python
# Zamiast: uc = CreateOrderUseCase(repo); order = await uc.execute(...)
# Teraz:
order_id = await mediator.send(CreateOrderCommand(...))   # Command
order    = await mediator.query(GetOrderQuery(...))        # Query
```

---

## Struktura każdego serwisu

```
serwis/
├── main.py
├── requirements.txt
└── app/
    ├── api/routes.py              ← FastAPI, używa Mediatora
    ├── core/
    │   ├── commands/              ← Command i Query klasy
    │   └── handlers.py            ← CommandHandler i QueryHandler
    ├── domain/models.py           ← encje domenowe
    └── infrastructure/
        ├── sqlite_repository.py   ← baza danych
        └── rabbitmq.py            ← broker
```

DesignService ma dodatkowo:
```
    └── infrastructure/
        └── s3_client.py           ← upload i presigned URL
```

---

## Uruchomienie

### 1. Skopiuj .env
```bash
cp .env.example .env
# uzupełnij wartości z CloudAMQP i AWS Learner Lab
```

### 2. Zainstaluj zależności
```bash
cd order_service && python -m pip install -r requirements.txt
cd design_service && python -m pip install -r requirements.txt
# itd. dla każdego serwisu
```

### 3. Uruchom (5 terminali)
```bash
# Terminal 1
cd order_service
python -m uvicorn main:app --port 8001 --reload

# Terminal 2
cd design_service
python -m uvicorn main:app --port 8002 --reload

# Terminal 3
cd inventory_service
python -m uvicorn main:app --port 8003 --reload

# Terminal 4
cd payment_service
python -m uvicorn main:app --port 8004 --reload

# Terminal 5
cd notification_service
python -m uvicorn main:app --port 8005 --reload
```

### 4. Ważne — .env musi być w katalogu serwisu
Skopiuj plik `.env` do każdego katalogu serwisu:
```bash
cp .env order_service/.env
cp .env design_service/.env
cp .env inventory_service/.env
cp .env payment_service/.env
cp .env notification_service/.env
```

---

## Nowe endpointy DesignService

| Method | URL | Opis |
|--------|-----|------|
| POST | /designs/upload | Upload pliku → zapisuje w S3 + metadane w DB |
| GET | /designs/{id}/download | Pobiera presigned URL z S3 (ważny 1h) |
| GET | /designs/{id} | Pobiera metadane pliku |
| GET | /designs/ | Lista plików (opcjonalnie ?order_id=) |

---

## Mediator — jak to działa

Plik `mediator.py` jest w katalogu głównym i importowany przez wszystkie serwisy.

```
routes.py
    → tworzy Mediator()
    → rejestruje handlery: m.register_command(CreateOrderCommand, CreateOrderHandler(repo))
    → wysyła: await m.send(CreateOrderCommand(...))    ← Command
    → pyta:   await m.query(GetOrderQuery(...))         ← Query
    
Mediator
    → sprawdza typ obiektu
    → przekazuje do właściwego handlera
    → handler wykonuje logikę i zwraca wynik
```

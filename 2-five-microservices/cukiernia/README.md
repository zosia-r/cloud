# System Obsługi Zamówień Cukierniczych 🎂

System 5 mikroserwisów w FastAPI z brokerem RabbitMQ (CloudAMQP).

## Architektura

```
Klient (Postman)
      │
      ├──► OrderService       :8001  →  kolejka: order.created
      ├──► DesignService      :8002  →  kolejka: design.uploaded
      ├──► InventoryService   :8003  →  kolejka: inventory.reserved
      ├──► PaymentService     :8004  →  kolejka: payment.processed
      └──► NotificationService:8005  ←  subskrybuje wszystkie kolejki
```

### Przepływ zamówienia (BPMN)
1. **OrderService** – tworzy rekord zamówienia (status=pending), publikuje `OrderEvent`
2. **DesignService** – odbiera plik graficzny od użytkownika, loguje nazwę i rozszerzenie, publikuje `DesignEvent`
3. **InventoryService** – weryfikuje stany magazynowe, rezerwuje składniki, publikuje `InventoryEvent`
4. **PaymentService** – autoryzuje płatność, publikuje `PaymentEvent`
5. **NotificationService** – subskrybuje wszystkie kolejki, wysyła powiadomienia do klienta

### Clean Architecture (każdy serwis)
```
app/
├── api/            ← warstwa API (FastAPI routes, Pydantic schemas)
├── core/           ← warstwa aplikacji (use cases / logika biznesowa)
├── domain/         ← warstwa domenowa (modele, interfejsy repozytoriów)
└── infrastructure/ ← warstwa infrastruktury (SQLite repo, RabbitMQ)
```

---

## Wymagania

- Python 3.11+
- Konto na [CloudAMQP](https://www.cloudamqp.com/) (darmowy plan "Little Lemur" wystarczy)

---

## Konfiguracja CloudAMQP

1. Zaloguj się na https://www.cloudamqp.com/ i utwórz nową instancję (plan **Little Lemur** – darmowy)
2. Skopiuj **AMQP URL** (zaczyna się od `amqps://...`)
3. Ustaw go jako zmienną środowiskową przed uruchomieniem:

```bash
export RABBITMQ_URL="amqps://user:haslo@host.cloudamqp.com/vhost"
```

---

## Uruchomienie lokalne

Każdy mikroserwis uruchamiamy w osobnym terminalu.

### 1. Instalacja zależności (raz per serwis)

```bash
# Terminal 1
cd order_service && pip install -r requirements.txt

# Terminal 2
cd design_service && pip install -r requirements.txt

# Terminal 3
cd inventory_service && pip install -r requirements.txt

# Terminal 4
cd payment_service && pip install -r requirements.txt

# Terminal 5
cd notification_service && pip install -r requirements.txt
```

### 2. Uruchomienie serwisów

```bash
# Terminal 1 - OrderService
cd order_service
export RABBITMQ_URL="amqps://..."
uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# Terminal 2 - DesignService
cd design_service
export RABBITMQ_URL="amqps://..."
uvicorn main:app --host 0.0.0.0 --port 8002 --reload

# Terminal 3 - InventoryService
cd inventory_service
export RABBITMQ_URL="amqps://..."
uvicorn main:app --host 0.0.0.0 --port 8003 --reload

# Terminal 4 - PaymentService
cd payment_service
export RABBITMQ_URL="amqps://..."
uvicorn main:app --host 0.0.0.0 --port 8004 --reload

# Terminal 5 - NotificationService
cd notification_service
export RABBITMQ_URL="amqps://..."
uvicorn main:app --host 0.0.0.0 --port 8005 --reload
```

### 3. Weryfikacja

Otwórz w przeglądarce:
- http://localhost:8001/docs  – OrderService Swagger UI
- http://localhost:8002/docs  – DesignService Swagger UI
- http://localhost:8003/docs  – InventoryService Swagger UI
- http://localhost:8004/docs  – PaymentService Swagger UI
- http://localhost:8005/docs  – NotificationService Swagger UI

---

## Bazy danych

Każdy serwis tworzy własny plik SQLite w katalogu roboczym:

| Serwis              | Plik bazy danych          |
|---------------------|---------------------------|
| OrderService        | `order_service.db`        |
| DesignService       | `design_service.db`       |
| InventoryService    | `inventory_service.db`    |
| PaymentService      | `payment_service.db`      |
| NotificationService | `notification_service.db` |

---

## Kolejki RabbitMQ

| Kolejka              | Producent           | Konsument              |
|----------------------|---------------------|------------------------|
| `order.created`      | OrderService        | NotificationService    |
| `design.uploaded`    | DesignService       | NotificationService    |
| `inventory.reserved` | InventoryService    | NotificationService    |
| `payment.processed`  | PaymentService      | NotificationService    |

---

## Postman

1. Zaimportuj plik `postman_collection.json` do Postmana
   (File → Import → wybierz plik)
2. W kolekcji są predefiniowane zmienne (URLs i `order_id`)
3. `order_id` jest automatycznie zapisywany po utworzeniu zamówienia

### Zalecana kolejność wywołań:
1. `TEST 1` – Utwórz nowe zamówienie (zapisuje `order_id`)
2. `TEST 2` – Aktualizuj status na confirmed
3. `TEST 3` – Wgraj plik graficzny (formularz multipart)
4. Zarezerwuj składniki
5. Zrealizuj płatność
6. Sprawdź powiadomienia

### Wymagane testy (min. 3):
| #  | Nazwa testu                                  | Serwis        |
|----|----------------------------------------------|---------------|
| T1 | Utwórz nowe zamówienie (status=pending, 201) | OrderService  |
| T2 | Aktualizuj status na confirmed               | OrderService  |
| T3 | Wgraj plik graficzny (extension w response)  | DesignService |

---

## Logi

Każdy serwis zapisuje logi do pliku `.log` i na stdout:

```
2024-01-15 12:00:01 | INFO | app.core.use_cases | CreateOrderUseCase: creating order for customer=Anna Kowalska
2024-01-15 12:00:01 | INFO | app.infrastructure.sqlite_repository | Saving order id=abc-123 to database
2024-01-15 12:00:01 | INFO | app.infrastructure.rabbitmq | Publishing message to queue: order.created
```

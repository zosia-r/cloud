#!/bin/bash

SERVICES=("order_service" "design_service" "inventory_service" "payment_service" "notification_service")

if [ ! -f ".env" ]; then
    echo "Błąd: plik .env nie istnieje w katalogu $(pwd)"
    exit 1
fi

for SERVICE in "${SERVICES[@]}"; do
    if [ -d "$SERVICE" ]; then
        cp -f .env "$SERVICE/.env"
        echo "✓ $SERVICE/.env zaktualizowany"
    else
        echo "⚠ Katalog $SERVICE nie istnieje — pominięto"
    fi
done

echo "Gotowe."
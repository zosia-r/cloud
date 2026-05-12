#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$ROOT_DIR/.env"
SERVICES_DIR="$ROOT_DIR/services"

SERVICES=("order_service" "design_service" "inventory_service" "payment_service" "notification_service")

if [ ! -f "$ENV_FILE" ]; then
    echo "Błąd: plik .env nie istnieje w katalogu $ROOT_DIR"
    exit 1
fi

for SERVICE in "${SERVICES[@]}"; do
    SERVICE_PATH="$SERVICES_DIR/$SERVICE"
    if [ -d "$SERVICE_PATH" ]; then
        cp -f "$ENV_FILE" "$SERVICE_PATH/.env"
        echo "✓ $SERVICE_PATH/.env zaktualizowany"
    else
        echo "⚠ Katalog $SERVICE_PATH nie istnieje — pominięto"
    fi
done

echo "Gotowe."

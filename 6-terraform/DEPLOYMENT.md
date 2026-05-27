# 🚀 Deployment - Wdrożenie aplikacji na AWS (instrukcja krok po kroku)

Deployment odbywa się w **2 etapach**:
1. **ETAP 1**: Tworzymy bazy danych i usługi przechowywania (RDS PostgreSQL, DynamoDB, S3, RabbitMQ)
2. **ETAP 2**: Deployujemy nasze serwisy (Order, Design, Inventory, Payment, Notification) na AWS

---

## ETAP 1️⃣ - Tworzenie baz danych na AWS

**Co się stanie**: Terraform utworzy na AWS:
- 📊 3 bazy PostgreSQL (order, inventory, payment)
- 📋 2 tabele DynamoDB (design, notification)
- 🪣 S3 bucket (do przechowywania plików projektów)
- 🐰 RabbitMQ (do komunikacji między serwisami)

### Krok 1: Otwórz folder stage1

```bash
cd 6-terraform/terraform/stage1
```

### Krok 2: Przygotuj plik konfiguracyjny terraform.tfvars


### Krok 3: Zaloguj się na AWS

Musisz najpierw zalogować się do AWS:

```bash
aws configure
```

### Krok 4: Uruchom Terraform ETAP 1

```bash
terraform init
```

To pobiera narzędzia Terraform (wykonaj raz).

Teraz tworzymy infrastrukturę:

```bash
terraform apply
```

Terraform pokaże plan co będzie tworzyć. Wpisz `yes` aby potwierdzić.

⏳ **To trwa 5-15 minut!** Czekaj aż zobaczysz:
```
Apply complete! Resources: XX added, 0 changed, 0 destroyed.
```

✅ **ETAP 1 GOTOWY!** Bazy danych zostały utworzone.

---

## ETAP 2️⃣ - Deployowanie serwisów

**Co się stanie**: 
1. Zbudujemy Docker obrazy (zrobisz ze swoim kodem)
2. Wrzucimy obrazy do AWS (ECR - to taki magazyn obrazów AWS)
3. Terraform uruchomi serwisy na AWS w chmurze

### KROK 1: Budowanie obrazów Docker (na swoim komputerze)

Przejdź do folderu docker:

```bash
cd 5-docker
```

Teraz zbuduj **po kolei** każdy obraz. Każda komenda buduje jeden serwis:

```bash
# Buduj order service
podman build -f docker/base/Dockerfile --build-arg SERVICE_DIR=services/order_service -t order:latest .

# Buduj design service
podman build -f docker/base/Dockerfile --build-arg SERVICE_DIR=services/design_service -t design:latest .

# Buduj inventory service
podman build -f docker/base/Dockerfile --build-arg SERVICE_DIR=services/inventory_service -t inventory:latest .

# Buduj payment service
podman build -f docker/base/Dockerfile --build-arg SERVICE_DIR=services/payment_service -t payment:latest .

# Buduj notification service
podman build -f docker/base/Dockerfile --build-arg SERVICE_DIR=services/notification_service -t notification:latest .
```

⏳ **To trwa kilka minut** (Docker pobiera bazowy obraz, instaluje zależności itp.)

Jak skończy, sprawdź czy się zbudowały:
```bash
podman images | grep -E "order|design|inventory|payment|notification"
```

Powinieneś zobaczyć 5 obrazów.

✅ **Obrazy Docker gotowe!**

---

### KROK 2: Przygotowanie AWS ECR (repozytorium obrazów)

ECR to jak GitHub ale dla obrazów Docker. Musisz tam wrzucić swoje obrazy.

Najpierw pobierz swój **AWS Account ID**:

```bash
aws sts get-caller-identity --query Account --output text
```

Zapisz tę liczbę, będziesz jej potrzebować. Na przykład: `123456789012`

Teraz utwórz repozytoria dla każdego serwisu:

```bash
aws ecr create-repository --repository-name order --region us-east-1
aws ecr create-repository --repository-name design --region us-east-1
aws ecr create-repository --repository-name inventory --region us-east-1
aws ecr create-repository --repository-name payment --region us-east-1
aws ecr create-repository --repository-name notification --region us-east-1
```

AWS odpowie że repozytoria zostały utworzone.

✅ **Repozytoria na AWS gotowe!**

---

### KROK 3: Zaloguj Docker do AWS

Teraz powiedz Dockerowi gdzie wrzucać obrazy (adres AWS):

```bash
aws ecr get-login-password --region us-east-1 | podman login --username AWS --password-stdin 265068570806.dkr.ecr.us-east-1.amazonaws.com
```

Gdy się zaloguje, powinieneś zobaczyć: `Login Succeeded`

✅ **Docker zalogowany!**

---

### KROK 4: Przygotuj obrazy i wrzuć je do AWS

Dla każdego serwisu musisz:
1. Zmienić etykietę (tag) obrazu na adres AWS
2. Wrzucić (push) do AWS

**Dla KAŻDEGO serwisu wykonaj**:

```bash
# ORDER SERVICE
podman tag order:latest 265068570806.dkr.ecr.us-east-1.amazonaws.com/order:latest
podman push 265068570806.dkr.ecr.us-east-1.amazonaws.com/order:latest

# DESIGN SERVICE
podman tag design:latest 265068570806.dkr.ecr.us-east-1.amazonaws.com/design:latest
podman push 265068570806.dkr.ecr.us-east-1.amazonaws.com/design:latest

# INVENTORY SERVICE
podman tag inventory:latest 265068570806.dkr.ecr.us-east-1.amazonaws.com/inventory:latest
podman push 265068570806.dkr.ecr.us-east-1.amazonaws.com/inventory:latest

# PAYMENT SERVICE
podman tag payment:latest 265068570806.dkr.ecr.us-east-1.amazonaws.com/payment:latest
podman push 265068570806.dkr.ecr.us-east-1.amazonaws.com/payment:latest

# NOTIFICATION SERVICE
podman tag notification:latest 265068570806.dkr.ecr.us-east-1.amazonaws.com/notification:latest
podman push 265068570806.dkr.ecr.us-east-1.amazonaws.com/notification:latest
```

⏳ **To trwa parę minut** (wrzucanie obrazów na AWS)

Jak się skończy, zobaczysz dla każdego: `Pushed`

✅ **Obrazy są na AWS!**

---

### KROK 5: Przygotuj Terraform do stage2

Przejdź do folderu:

```bash
cd 6-terraform/terraform/stage2
```

Skonfiguruj plik konfiguracyjny `terraform.tfvars`:


✅ **Konfiguracja stage2 gotowa!**

---

### KROK 6: Uruchom Terraform ETAP 2

```bash
terraform init
```

```bash
terraform apply
```

Wpisz `yes` aby potwierdzić.

⏳ **To trwa 10-20 minut!** Terraform będzie:
- Tworzyć ECS Cluster
- Tworzyć Load Balancer
- Deployować serwisy

Czekaj aż zobaczysz:
```
Apply complete! Resources: XX added, 0 changed, 0 destroyed.
```

---

### KROK 7: Sprawdź adresy serwisów

Po skończeniu, pokaż output:

```bash
terraform output
```

Lub konkretnie adresy serwisów:

```bash
terraform output service_urls
```

Zobaczysz coś takiego:
```
service_urls = {
  "design"       = "http://cukiernia-alb-12345.us-east-1.elb.amazonaws.com:8002"
  "inventory"    = "http://cukiernia-alb-12345.us-east-1.elb.amazonaws.com:8003"
  "notification" = "http://cukiernia-alb-12345.us-east-1.elb.amazonaws.com:8005"
  "order"        = "http://cukiernia-alb-12345.us-east-1.elb.amazonaws.com:8001"
  "payment"      = "http://cukiernia-alb-12345.us-east-1.elb.amazonaws.com:8004"
}
```

✅ **To są adresy Twoich serwisów na AWS!**

Możesz je otworzyć w przeglądarce (dodaj `/health` na końcu aby sprawdzić czy serwis żyje):
- `http://cukiernia-alb-12345.us-east-1.elb.amazonaws.com:8001/health`

Można testować Postmanem:
collection -> variables -> zmienić url wszystkich serwisów na te z aws

---

## 🎉 GOTOWE!

Twoja aplikacja "Cukiernia" jest na AWS w chmurze!

⚠️ **Pamiętaj**: Jak skończysz testować, usuń infrastrukturę:
```bash
cd 6-terraform/terraform/stage2
terraform destroy
cd ../stage1
terraform destroy
```

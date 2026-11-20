# Architecture Web Distribuée – Eureka Server + Observabilité (Actuator)

**Équipe :** _Nom Prénom 1_, _Nom Prénom 2_, _Nom Prénom 3_  
**Année universitaire :** 2026-2027

Ce dépôt regroupe les deux ateliers :
1. **Implémentation « Eureka server »** : serveur de découverte + enregistrement des microservices.
2. **Observabilité avec Spring Boot Actuator** : santé, info, métriques, loggers, HealthIndicator personnalisé, santé publiée dans Eureka.

## 1. Architecture

| Microservice | Technologie | Port | Nom dans Eureka | Dossier |
|---|---|---|---|---|
| Eureka Server | Spring Boot 3.2.5 / Cloud 2023.0.4 | 8761 | – | `eureka-server/` |
| Candidat | Spring Boot + H2 | 8081 | CANDIDAT | `microservices/candidat/` |
| Job | Spring Boot + MySQL | 8082 | JOB | `microservices/job/` |
| Candidature | Spring Boot | 8085 | CANDITATURE | `microservices/canditature/` |
| Meeting | Node.js / Express | 8083 | MEETING | `microservices/meeting/` |
| Notification | Python / FastAPI | 8084 | NOTIFICATION | `microservices/notification/` |

**Ordre de démarrage :** MySQL (XAMPP/WAMP) → Eureka Server → Candidat, Candidature, Job → Meeting, Notification.

```bash
# Eureka + services Spring (un terminal chacun)
cd eureka-server && mvn spring-boot:run
cd microservices/candidat && mvn spring-boot:run
cd microservices/canditature && mvn spring-boot:run
cd microservices/job && mvn spring-boot:run

# Meeting (Node.js)
cd microservices/meeting && npm install && npm start

# Notification (Python)
cd microservices/notification
python -m venv venv && .\venv\Scripts\Activate.ps1      # Linux/Mac : source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --port 8084
```

---

## 2. Atelier 1 – Eureka Server

### Partie 1 : serveur Eureka (`eureka-server/`)
- Dépendance `spring-cloud-starter-netflix-eureka-server` dans le `pom.xml`.
- Annotation `@EnableEurekaServer` sur `EurekaApplication`.
- `application.properties` :
  ```properties
  spring.application.name=eureka
  server.port=8761
  eureka.client.register-with-eureka=false
  eureka.client.fetch-registry=false
  ```
- Dashboard : http://localhost:8761

📸 **Capture 1** – dashboard vide (« No instances available ») → `docs/screenshots/01-eureka-vide.png`

### Partie 2 : clients Eureka (Candidat, Job, Candidature)
- Dépendance `spring-cloud-starter-netflix-eureka-client` ajoutée aux trois `pom.xml`.
- `@EnableDiscoveryClient` sur les classes `*Application`.
- Configuration (`application.properties`) :
  ```properties
  eureka.client.service-url.defaultZone=http://localhost:8761/eureka
  eureka.client.register-with-eureka=true
  eureka.client.fetch-registry=true
  eureka.instance.prefer-ip-address=true
  ```

📸 **Capture 2** – CANDIDAT, JOB et CANDITATURE `UP` dans le dashboard → `docs/screenshots/02-eureka-spring.png`

**Deuxième instance de Candidat** (montée en charge) :
```bash
cd microservices/candidat
mvn spring-boot:run -Dspring-boot.run.arguments=--server.port=8091
```
📸 **Capture 3** – CANDIDAT avec `(2)` instances (8081 et 8091) → `docs/screenshots/03-candidat-2-instances.png`

### Partie 3 : Meeting (Node.js) et Notification (Python)
- **Meeting** : `eureka-js-client` (`npm install eureka-js-client`), configuration dans `src/config/eureka.js`, démarrage dans `src/server.js`. Le port est lu depuis `PORT`.
- **Notification** : `py-eureka-client` dans `requirements.txt`, enregistrement dans le `lifespan` de FastAPI (`app/main.py`), arrêt du client à l'arrêt de l'application. Le port est lu depuis `PORT`.

Lancer plusieurs instances :
```bash
# Meeting
PORT=8093 npm start                   # PowerShell : $env:PORT=8093; npm start
# Notification
PORT=8094 python -m uvicorn app.main:app --port 8094     # PowerShell : $env:PORT=8094; ...
```

📸 **Capture 4** – dashboard avec les 5 services + au moins **2 instances** de MEETING ou NOTIFICATION → `docs/screenshots/04-eureka-complet.png`

---

## 3. Atelier 2 – Observabilité avec Actuator

### Partie 1 : mise en place
Dépendance ajoutée dans `candidat`, `job` et `canditature` :
```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-actuator</artifactId>
</dependency>
```
Configuration commune (`application.properties`) :
```properties
management.endpoints.web.exposure.include=health,info,metrics,loggers
management.endpoint.health.show-details=always
eureka.client.healthcheck.enabled=true      # Eureka reçoit le vrai statut de /health
management.info.env.enabled=true
info.app.name=job
info.app.version=1.0.0
info.app.description=Microservice de gestion des offres
```

📸 **Capture 5** – `http://localhost:8081/actuator/health` → `docs/screenshots/05-candidat-health.png`

### Partie 2 : lire l'état d'un microservice

**Étape 1 – `/actuator/health` (Job)** : `http://localhost:8082/actuator/health`  
Résultat attendu : statut `UP` avec les composants `db`, `diskSpace`, `jobsTable` (notre indicateur), `ping`…

📸 **Capture 6** – `http://localhost:8082/actuator/health` (UP) → `docs/screenshots/06-job-health-up.png`

**Étape 2 – panne de la base MySQL**
1. Arrêter MySQL dans XAMPP/WAMP.
2. Rappeler `http://localhost:8082/actuator/health` → statut global `DOWN` (HTTP 503), composant `db` en `DOWN`.
3. Ouvrir http://localhost:8761 → **JOB** passe à `DOWN`.
4. Redémarrer MySQL → JOB repasse `UP`.

📸 **Capture 7** – `/actuator/health` de Job en `DOWN` → `docs/screenshots/07-job-health-down.png`  
📸 **Capture 8** – dashboard Eureka avec JOB `DOWN (1)` → `docs/screenshots/08-eureka-job-down.png`  
📸 **Capture 9** – JOB de nouveau `UP` après redémarrage de MySQL → `docs/screenshots/09-eureka-job-up.png`

**Étape 3 – `/actuator/info` (Candidat)** : `http://localhost:8081/actuator/info`
```json
{ "app": { "name": "candidat", "version": "1.0.0",
           "description": "Microservice de gestion des candidats", "team": "Nom de votre equipe" } }
```
(le lien de chaque instance dans le dashboard Eureka pointe vers `/actuator/info`)

📸 **Capture 10** – `/actuator/info` → `docs/screenshots/10-candidat-info.png`

**Étape 4 – `/actuator/metrics`**
1. `http://localhost:8081/actuator/metrics` : liste des métriques.
2. `http://localhost:8081/actuator/metrics/jvm.memory.used`.
3. Appeler plusieurs fois `GET http://localhost:8081/api/...` (liste des candidats), puis ouvrir `http://localhost:8081/actuator/metrics/http.server.requests`.

📸 **Capture 11** – `http.server.requests` → `docs/screenshots/11-metrics-http-requests.png`  
📸 **Capture 12** – `http.server.requests?tag=status:200` → `docs/screenshots/12-metrics-status-200.png`

**Réponses aux questions** _(à compléter avec VOS valeurs après les appels)_ :
- Nombre de requêtes HTTP traitées (mesure `COUNT`) : **…**
- Durée de la requête la plus lente (mesure `MAX`, en secondes) : **…**
- `?tag=status:200` : ne compte que les requêtes ayant répondu **HTTP 200** (le `COUNT` est donc ≤ au total, car les 404/500 sont exclues).

### Loggers (modifier le niveau de logs sans redémarrer)
L'endpoint `loggers` est exposé (`management.endpoints.web.exposure.include=...,loggers`).
```bash
# Lire le niveau actuel
curl http://localhost:8081/actuator/loggers/com.awd.candidat
# Passer en DEBUG à chaud
curl -X POST http://localhost:8081/actuator/loggers/com.awd.candidat \
     -H "Content-Type: application/json" -d '{"configuredLevel":"DEBUG"}'
# Revenir à la configuration par défaut
curl -X POST http://localhost:8081/actuator/loggers/com.awd.candidat \
     -H "Content-Type: application/json" -d '{"configuredLevel":null}'
```
📸 **Capture 13** – `configuredLevel` = `DEBUG` après le POST → `docs/screenshots/13-loggers-debug.png`

### HealthIndicator personnalisé (Job)
`microservices/job/src/main/java/com/awd/job/health/JobsTableHealthIndicator.java` : vérifie que la table `job` est lisible (`jobRepository.count()`). Il apparaît dans `/actuator/health` sous la clé `jobsTable` et fait passer le service `DOWN` si la table est illisible.

### Partie 5 : santé des services Node.js et Python

**Meeting (Node.js / Express)**
- `GET /health` → `200 {"status":"UP"}`
- `GET /info` → nom + version lus dans `package.json`
- `healthCheckUrl` et `statusPageUrl` déclarés dans `src/config/eureka.js`.

**Notification (Python / FastAPI)**
- `GET /health` et `GET /info` dans `app/main.py`.
- `health_check_url` et `status_page_url` passés à `eureka_client.init_async(...)`.
- Vérification : `GET http://localhost:8761/eureka/apps/NOTIFICATION` doit contenir les deux URL.

#### Vérification réalisée (sorties réelles de nos tests locaux)
```text
$ curl http://localhost:8083/health            -> {"status":"UP"}  (HTTP 200)
$ curl http://localhost:8083/info              -> {"name":"meeting","version":"1.0.0","description":"Meeting microservice (Node.js / Express) ..."}
$ curl http://localhost:8083/api/meetings/hello      -> {"message":"hello I'm microservice meeting"}
$ curl http://localhost:8084/health            -> {"status":"UP"}  (HTTP 200)
$ curl http://localhost:8084/info              -> {"name":"notification","version":"1.0.0","description":"Microservice de notifications"}
$ curl http://localhost:8084/api/notifications/hello -> {"message":"hello I'm microservice notification"}
```
Tests automatiques : `node --test test/hello.test.js` (6/6 OK) et `pytest` (6/6 OK).  
Si le serveur Eureka est arrêté, Meeting et Notification continuent de répondre (l'échec d'enregistrement est seulement journalisé).

📸 **Capture 14** – dashboard : liens MEETING et NOTIFICATION → `/info` → `docs/screenshots/14-meeting-notification-info.png`  
📸 **Capture 15** – `http://localhost:8761/eureka/apps/NOTIFICATION` (avec `healthCheckUrl` et `statusPageUrl`) → `docs/screenshots/15-registry-notification.png`

---

## 4. Checklist du rendu (note CC)
- [ ] Eureka Server fonctionnel
- [ ] Candidat, Job, Candidature, Meeting, Notification visibles dans le dashboard (captures 2 et 4)
- [ ] ≥ 2 instances de MEETING ou NOTIFICATION (capture 4)
- [ ] Actuator sur Candidat, Job, Candidature (captures 5 à 13)
- [ ] Partie 5 finalisée (captures 14 et 15)
- [ ] Noms des membres de l'équipe en haut de ce README
- [ ] Projet poussé sur GitHub

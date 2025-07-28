# Security Features Documentation

## Übersicht

Die MetaMCP Security Features bieten umfassende Sicherheitsfunktionen für die Plattform, einschließlich Policy-basierter Zugriffskontrolle, Rate Limiting, IP-Filtering und erweiterte Monitoring-Funktionen.

## 🛡️ Policy Engine

### Grundlagen

Die Policy Engine verwendet Open Policy Agent (OPA) für deklarative Zugriffskontrolle mit Rego-Policies.

```python
from metamcp.security.policies import PolicyEngine
from metamcp.config import PolicyEngineType

# Policy Engine initialisieren
policy_engine = PolicyEngine(PolicyEngineType.OPA, opa_url="http://localhost:8181")
await policy_engine.initialize()
```

### Vordefinierte Policies

#### 1. Tool Access Policy
```rego
package metamcp.tool_access

default allow = false

allow {
    input.action == "read"
    input.resource = startswith("tool:")
    input.user.role == "user"
}

allow {
    input.action == "execute"
    input.resource = startswith("tool:")
    input.user.role == "user"
    input.user.permissions[_] == "tool_execute"
}

allow {
    input.action == "manage"
    input.resource = startswith("tool:")
    input.user.role == "admin"
}
```

#### 2. Data Access Policy
```rego
package metamcp.data_access

default allow = false

allow {
    input.action == "read"
    input.resource = startswith("data:public:")
}

allow {
    input.action == "read"
    input.resource = startswith("data:user:")
    input.user.id == input.resource_user_id
}

allow {
    input.action == "write"
    input.resource = startswith("data:user:")
    input.user.id == input.resource_user_id
    input.user.permissions[_] == "data_write"
}
```

#### 3. Rate Limiting Policy
```rego
package metamcp.rate_limiting

default allow = true

allow = false {
    input.rate_limit_exceeded == true
}

rate_limit_exceeded {
    input.request_count > input.limit
    input.window_start < time.now_ns()
}
```

### Policy-Versionierung

```python
# Neue Policy erstellen
version_id = await policy_engine.create_policy(
    "custom_policy",
    policy_content,
    "Beschreibung der Policy",
    "user_id"
)

# Policy aktualisieren
new_version_id = await policy_engine.update_policy(
    "custom_policy",
    updated_content,
    "Aktualisierte Beschreibung",
    "user_id"
)

# Policy-Version aktivieren
success = await policy_engine.activate_policy_version("custom_policy", version_id)
```

### Zugriffskontrolle mit Kontext

```python
# Erweiterte Zugriffskontrolle mit IP, Rate Limiting und Quotas
context = {
    "ip": "192.168.1.100",
    "rate_limit_key": "user1",
    "limit": 100,
    "quota_key": "user1",
    "usage": 500,
    "limit": 1000
}

result = await policy_engine.check_access(
    user_id="user1",
    resource="tool:calculator",
    action="execute",
    context=context
)
```

## 🚦 Rate Limiting

### Strategien

#### 1. Fixed Window
```python
from metamcp.security.rate_limiting import RateLimiter, RateLimitConfig, RateLimitStrategy

config = RateLimitConfig(
    key="user1",
    limit=100,
    window_seconds=60,
    strategy=RateLimitStrategy.FIXED_WINDOW
)
```

#### 2. Sliding Window
```python
config = RateLimitConfig(
    key="user1",
    limit=100,
    window_seconds=60,
    strategy=RateLimitStrategy.SLIDING_WINDOW
)
```

#### 3. Token Bucket
```python
config = RateLimitConfig(
    key="user1",
    limit=100,
    window_seconds=60,
    strategy=RateLimitStrategy.TOKEN_BUCKET,
    burst_limit=50
)
```

#### 4. Leaky Bucket
```python
config = RateLimitConfig(
    key="user1",
    limit=100,
    window_seconds=60,
    strategy=RateLimitStrategy.LEAKY_BUCKET
)
```

### Verwendung

```python
# Rate Limiter initialisieren
rate_limiter = RateLimiter()
await rate_limiter.initialize()

# Rate Limit hinzufügen
await rate_limiter.add_rate_limit(config)

# Rate Limit prüfen
result = await rate_limiter.check_rate_limit("user1", cost=1)

if result.allowed:
    # Request verarbeiten
    pass
else:
    # Request ablehnen
    retry_after = result.retry_after
```

### Middleware Integration

```python
from metamcp.security.rate_limiting import RateLimitMiddleware

# Middleware erstellen
middleware = RateLimitMiddleware(rate_limiter)

# In FastAPI App
app.add_middleware(middleware)
```

## 🔒 IP-Filtering

### Whitelist/Blacklist Management

```python
# IP zur Whitelist hinzufügen
await policy_engine.add_ip_to_whitelist("192.168.1.100")

# IP zur Blacklist hinzufügen
await policy_engine.add_ip_to_blacklist("10.0.0.50")

# IP aus Whitelist entfernen
await policy_engine.remove_ip_from_whitelist("192.168.1.100")

# IP aus Blacklist entfernen
await policy_engine.remove_ip_from_blacklist("10.0.0.50")

# Aktuelle Listen abrufen
lists = await policy_engine.get_ip_lists()
```

## 🧪 Policy Testing

### Policy Tester

```python
from metamcp.security.policy_tester import PolicyTester

# Policy Tester initialisieren
tester = PolicyTester(policy_engine)
await tester.add_predefined_test_cases()

# Policy-Syntax validieren
is_valid, errors = await tester.validate_policy_syntax(policy_content)

# Test Case hinzufügen
test_case = PolicyTestCase(
    name="admin_access_test",
    description="Test admin access to tools",
    input_data={
        "user": {"id": "admin1", "role": "admin"},
        "resource": "tool:calculator",
        "action": "manage"
    },
    expected_result=True,
    tags=["admin", "positive"]
)

await tester.add_test_case("tool_access", test_case)

# Tests ausführen
results = await tester.run_policy_tests("tool_access")

# Test Report generieren
report = await tester.generate_test_report(results)

# Ergebnisse exportieren
json_export = await tester.export_test_results("json")
csv_export = await tester.export_test_results("csv")
```

### Vordefinierte Test Cases

Der Policy Tester kommt mit vordefinierten Test Cases für:

- **Tool Access**: Benutzer- und Admin-Zugriff auf Tools
- **Rate Limiting**: Rate Limit Überschreitung
- **Data Access**: Öffentliche und private Datenzugriffe
- **Permissions**: Berechtigungs-basierte Zugriffe

## 📊 Monitoring und Statistiken

### Policy Engine Statistiken

```python
# Policy-Versionen abrufen
versions = await policy_engine.get_policy_versions("tool_access")

# Policy-Status abrufen
status = await policy_engine.get_rate_limit_status("user1")
```

### Rate Limiter Statistiken

```python
# Alle Rate Limits abrufen
all_limits = await rate_limiter.get_all_rate_limits()

# Statistiken abrufen
stats = await rate_limiter.get_statistics()
```

### Policy Tester Statistiken

```python
# Test-Statistiken abrufen
stats = await tester.get_test_statistics()

# Coverage berechnen
coverage = await tester.calculate_policy_coverage()
```

## 🔧 Konfiguration

### Policy Engine Konfiguration

```python
# OPA-basierte Policy Engine
policy_engine = PolicyEngine(
    engine_type=PolicyEngineType.OPA,
    opa_url="http://localhost:8181"
)

# Interne Policy Engine (Fallback)
policy_engine = PolicyEngine(
    engine_type=PolicyEngineType.INTERNAL
)
```

### Rate Limiter Konfiguration

```python
# Globale Konfiguration
rate_limiter.global_config = {
    "default_limit": 100,
    "default_window": 60,
    "default_strategy": RateLimitStrategy.FIXED_WINDOW,
    "enable_monitoring": True,
    "cleanup_interval": 3600
}
```

## 🚀 Best Practices

### 1. Policy Design

- **Least Privilege**: Nur minimale notwendige Berechtigungen gewähren
- **Separation of Concerns**: Separate Policies für verschiedene Ressourcen
- **Versionierung**: Immer Policy-Versionen verwenden für Rollbacks
- **Testing**: Umfassende Tests für alle Policies schreiben

### 2. Rate Limiting

- **Appropriate Limits**: Limits basierend auf Business-Anforderungen setzen
- **Strategy Selection**: Passende Rate Limiting-Strategie wählen
- **Monitoring**: Rate Limiting-Metriken überwachen
- **Graceful Degradation**: Benutzerfreundliche Fehlermeldungen

### 3. IP-Filtering

- **Whitelist First**: Whitelist-Ansatz für kritische Systeme
- **Regular Updates**: IP-Listen regelmäßig aktualisieren
- **Logging**: Alle IP-Filtering-Aktionen loggen
- **Fallback**: Fallback-Mechanismen für legitime Benutzer

### 4. Testing

- **Comprehensive Coverage**: Alle Policy-Pfade testen
- **Edge Cases**: Grenzfälle und Fehlerszenarien testen
- **Performance**: Performance-Tests für Policies
- **Automation**: Automatisierte Tests in CI/CD-Pipeline

## 🔍 Troubleshooting

### Häufige Probleme

#### 1. Policy Engine nicht initialisiert
```python
# Prüfen ob Policy Engine initialisiert ist
if not policy_engine.is_initialized:
    await policy_engine.initialize()
```

#### 2. OPA-Verbindung fehlgeschlagen
```python
# OPA-Server Status prüfen
try:
    response = await http_client.get("http://localhost:8181/health")
    if response.status_code != 200:
        # Fallback auf interne Engine
        policy_engine = PolicyEngine(PolicyEngineType.INTERNAL)
except Exception:
    # Fallback auf interne Engine
    policy_engine = PolicyEngine(PolicyEngineType.INTERNAL)
```

#### 3. Rate Limiting funktioniert nicht
```python
# Rate Limiter Status prüfen
status = await rate_limiter.get_rate_limit_status("user1")
if status is None:
    # Rate Limit neu konfigurieren
    await rate_limiter.add_rate_limit(config)
```

#### 4. Policy Tests schlagen fehl
```python
# Policy-Syntax validieren
is_valid, errors = await tester.validate_policy_syntax(policy_content)
if not is_valid:
    print("Policy-Syntax-Fehler:", errors)
```

## 📈 Performance-Optimierung

### 1. Policy Caching

```python
# Aktive Policies werden automatisch gecacht
active_policies = policy_engine.active_policies
```

### 2. Rate Limiting Optimierung

```python
# Cleanup-Intervall anpassen
rate_limiter.global_config["cleanup_interval"] = 1800  # 30 Minuten
```

### 3. Test-Optimierung

```python
# Nur relevante Tests ausführen
results = await tester.run_policy_tests("specific_policy")
```

## 🔐 Sicherheitsrichtlinien

### 1. Policy-Sicherheit

- **Input Validation**: Alle Inputs validieren
- **Output Sanitization**: Ausgaben bereinigen
- **Audit Logging**: Alle Policy-Entscheidungen loggen
- **Regular Reviews**: Policies regelmäßig überprüfen

### 2. Rate Limiting-Sicherheit

- **DDoS Protection**: Angemessene Limits für DDoS-Schutz
- **Burst Handling**: Burst-Limits für legitime Spitzen
- **Monitoring**: Anomalie-Erkennung implementieren
- **Alerting**: Automatische Benachrichtigungen bei Überschreitungen

### 3. IP-Filtering-Sicherheit

- **Geolocation**: Geografische Beschränkungen
- **Reputation**: IP-Reputation prüfen
- **Dynamic Updates**: Dynamische IP-Listen
- **False Positive Handling**: Falsch-positive minimieren

## 📚 Weiterführende Ressourcen

- [Open Policy Agent Documentation](https://www.openpolicyagent.org/docs/)
- [Rego Language Reference](https://www.openpolicyagent.org/docs/latest/policy-language/)
- [Rate Limiting Patterns](https://cloud.google.com/architecture/rate-limiting-strategies-techniques)
- [Security Best Practices](https://owasp.org/www-project-api-security/)

## 🤝 Support

Bei Fragen oder Problemen mit den Security Features:

1. **Dokumentation**: Diese Dokumentation durchgehen
2. **Tests**: Unit-Tests für ähnliche Szenarien ausführen
3. **Logs**: Anwendungs-Logs auf Fehler prüfen
4. **Community**: GitHub Issues für bekannte Probleme prüfen
5. **Support**: Support-Team kontaktieren mit detaillierten Informationen
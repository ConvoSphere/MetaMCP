# Security & Authentication

Security-Architektur für MetaMCP mit Fokus auf Service-zu-Service Kommunikation und Agent-basierte Berechtigungen.

## 🎯 **Anforderungen**

### **Core Requirements**
- **Service-orientiert**: MetaMCP dient primär anderen Services/Projekten
- **Agent-basiert**: Tools werden von Agenten ausgeführt, nicht direkt von Usern
- **User-Agent-Beziehung**: Jeder Agent gehört zu einem User (kann wechseln)
- **Berechtigungsvererbung**: Agenten erben Rechte von Usern, können keine zusätzlichen Rechte haben
- **Tool-spezifische Berechtigungen**: Verschiedene User haben verschiedene Rechte auf gleiche Tools
- **Multi-Instance**: Mehrere Instanzen des gleichen Agent-Typs möglich (verschiedene User)

### **Security Constraints**
- **Unveränderliche Berechtigungen**: Berechtigungen dürfen sich während Session/Ausführung nicht ändern
- **Strikte Vererbung**: Agenten können keine Rechte haben, die der User nicht besitzt
- **Audit-Pflicht**: Vollständige Logging-Kette: User → Agent → Tool → Aktion

## 🏗️ **Architektur-Übersicht**

```
User (Owner)
├── Agent Instance 1 (erbt User-Rechte)
│   ├── Tool A: read
│   └── Tool B: read+write
├── Agent Instance 2 (erbt User-Rechte)
│   ├── Tool A: read
│   └── Tool C: execute
└── Agent Instance 3 (anderer User, gleicher Agent-Typ)
    ├── Tool A: read+write (andere User-Berechtigung)
    └── Tool D: admin
```

## ❓ **Offene Fragen**

### **1. Agent-Identifikation & Instanzen**
- [ ] **Agent-Instanz Identifikation**
  - Eindeutige Agent-ID pro Instanz? (`agent_123_instance_456`)
  - Oder Agent-Typ + User-Kombination? (`code_analyzer_user_789`)
  - Agent-Registry mit Metadaten erforderlich?

### **2. User-Berechtigungen Basis**
- [ ] **Berechtigungsmodell**
  - Direkt pro User pro Tool? (User X → Tool Z: read+write)
  - Role-basiert? (User X hat Rolle "Developer" → alle Dev-Tools)
  - Kombination aus Rollen + spezifische Overrides?

### **3. Berechtigungsgranularität**
- [ ] **Berechtigungsstufen**
  - Standard: `read`, `write`, `execute`, `delete`?
  - Spezifische: `query`, `modify`, `admin`?
  - Tool-spezifische Berechtigungen? (`database.query`, `database.modify`)

### **4. Agent-Wechsel Szenarien**
- [ ] **User-Wechsel Handling**
  - Sofortige Berechtigungsänderung?
  - Grace Period für laufende Operationen?
  - Session-Terminierung bei User-Wechsel?

### **5. Tool-Ausführungskontext**
- [ ] **Request-Payload Struktur**
  ```json
  {
    "user_id": "user_123",
    "agent_id": "agent_456_instance_789", 
    "agent_type": "code_analyzer",
    "tool_id": "tool_z",
    "action": "read"
  }
  ```

### **6. Caching & Performance**
- [ ] **Berechtigungs-Caching**
  - User-Berechtigungen für Session-Dauer?
  - Agent-Berechtigungen pro Request?
  - Cache-Invalidation bei User-Wechsel?

### **7. Audit & Compliance**
- [ ] **Logging-Anforderungen**
  - User → Agent → Tool → Aktion Kette?
  - Berechtigungsprüfung (erfolgreich/fehlgeschlagen)?
  - Timestamp, Session-ID, Request-ID?

### **8. Error Handling**
- [ ] **Fehlerbehandlung**
  - HTTP 403 Forbidden?
  - Detaillierte Fehlermeldungen?
  - Security-Monitoring Integration?

### **9. API-Design**
- [ ] **Tool-Ausführung API**
  ```bash
  POST /api/v1/tools/{tool_id}/execute
  {
    "user_id": "user_123",
    "agent_id": "agent_456",
    "parameters": {...}
  }
  ```

## 📊 **Aktueller Status**

### **✅ Implementiert**
- [x] Basis AuthService (`metamcp/services/auth_service.py`)
- [x] JWT Token Authentication
- [x] User Management (CRUD)
- [x] Password Hashing (bcrypt)
- [x] Basic Role System

### **🔄 In Arbeit**
- [ ] Agent Management System
- [ ] Tool Permission System
- [ ] Permission Inheritance Logic
- [ ] Audit Logging

### **❌ Nicht implementiert**
- [ ] Agent-User Relationship Management
- [ ] Tool-specific Permission Checks
- [ ] Agent Instance Tracking
- [ ] Permission Caching
- [ ] Security Audit Trail
- [ ] API Rate Limiting per User/Agent

## 🗄️ **Datenmodelle (Vorschläge)**

### **Option A: Direkte User-Tool Berechtigungen**
```sql
-- User-Tool Permissions
user_tool_permissions:
- user_id (FK)
- tool_id (FK)
- permissions (JSON: ["read", "write"])
- created_at
- updated_at

-- Agent Instances
agent_instances:
- agent_id (PK)
- agent_type
- user_id (FK, current owner)
- created_at
- last_activity
- metadata (JSON)

-- Agent Sessions
agent_sessions:
- session_id (PK)
- agent_id (FK)
- user_id (FK)
- created_at
- expires_at
- is_active
```

### **Option B: Role-basiert mit Overrides**
```sql
-- User Roles
user_roles:
- user_id (FK)
- role_id (FK)
- granted_at

-- Role Tool Permissions
role_tool_permissions:
- role_id (FK)
- tool_id (FK)
- permissions

-- User Tool Overrides
user_tool_overrides:
- user_id (FK)
- tool_id (FK)
- permissions (override role permissions)
```

## 🔧 **Implementierungsplan**

### **Phase 1: Foundation**
1. [ ] Agent Management Service
2. [ ] Tool Permission Service
3. [ ] Permission Inheritance Logic
4. [ ] Basic Audit Logging

### **Phase 2: Integration**
1. [ ] API Middleware für Permission Checks
2. [ ] Tool Execution mit Permission Validation
3. [ ] Agent Session Management
4. [ ] User-Agent Relationship Tracking

### **Phase 3: Advanced Features**
1. [ ] Permission Caching
2. [ ] Advanced Audit Trail
3. [ ] Security Monitoring
4. [ ] Rate Limiting per User/Agent

### **Phase 4: Testing & Validation**
1. [ ] Security Test Suite
2. [ ] Permission Inheritance Tests
3. [ ] Agent Switching Tests
4. [ ] Performance Tests

## 🧪 **Test-Szenarien**

### **Berechtigungsvererbung**
```python
# Test: Agent erbt User-Rechte
user = create_user(permissions={"tool_a": ["read"]})
agent = create_agent(user_id=user.id)
assert can_access(agent, "tool_a", "read") == True
assert can_access(agent, "tool_a", "write") == False
```

### **Agent-Wechsel**
```python
# Test: Agent wechselt User
user1 = create_user(permissions={"tool_a": ["read"]})
user2 = create_user(permissions={"tool_a": ["read", "write"]})
agent = create_agent(user_id=user1.id)

# Vor Wechsel
assert can_access(agent, "tool_a", "write") == False

# Nach Wechsel
agent.user_id = user2.id
assert can_access(agent, "tool_a", "write") == True
```

### **Multi-Instance**
```python
# Test: Verschiedene Agent-Instanzen
user1 = create_user(permissions={"tool_a": ["read"]})
user2 = create_user(permissions={"tool_a": ["read", "write"]})

agent1 = create_agent(user_id=user1.id, agent_type="analyzer")
agent2 = create_agent(user_id=user2.id, agent_type="analyzer")

assert can_access(agent1, "tool_a", "write") == False
assert can_access(agent2, "tool_a", "write") == True
```

## 📋 **Nächste Schritte**

1. **Klarungsfragen beantworten** - Alle offenen Fragen mit Stakeholdern klären
2. **Datenmodell finalisieren** - Entscheidung zwischen Option A/B oder Hybrid
3. **API-Spec definieren** - Tool Execution API und Permission Check Endpoints
4. **Implementierung starten** - Phase 1 des Implementierungsplans
5. **Test-Suite aufbauen** - Security-Tests parallel zur Entwicklung

## 🔗 **Verwandte Dokumentation**

- [API Reference](api.md) - REST API Dokumentation
- [Configuration](configuration.md) - Security-Konfiguration
- [Development Guide](development.md) - Entwickler-Guide
- [Admin Interface](admin-interface.md) - Security-Admin-Interface
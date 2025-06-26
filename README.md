## El proyecto

## Resumen de Relaciones y Flujos Clave

### Roles de Usuario:

1. **Administrador (Plataforma):**
   - `users.is_admin = TRUE`
   - Puede crear y editar organizaciones y asignar/desasignar a usuarios registrados en la plataforma como administradores
   - Puede crear y editar actividades.

2. **Usuario Normal:**
   - `users.is_admin = FALSE`
   - Un usuario ya registrado que no es un administrador de la plataforma, puede unirse a organizaciones, crear equipos, unirse a equipos.
   - Puede ser seleccionado como organizador de una organización por parte del administrador.
   - Puede ser seleccionado como árbitro de un torneo en específico dentro de una organización específica, por parte del organizador de esa misma organización.

3. **Organizador (de Organización):**
   - `organization_members.is_organizer = TRUE` para una `organization_id` específica
   - Puede crear torneos y eventos dentro de su organización (donde fue asignado).
   - Puede asignar árbitros a esos torneos en específico (a partir de los usuarios que se hayan unido a esa `organization_id`).

4. **Árbitro (de Torneo):**
   - Existe una entrada en `tournament_referees` para un `tournament_id` específico que enlaza usuarios con torneos
   - Aplica solo si no es admin, no es organizador de la misma organización, ni tampoco es jugador en el mismo torneo.
   - Puede registrar/editar resultados de partidos en ese torneo mientras la siguiente llave no esté lista. Se restringe la acción si el torneo no ha comenzado, ha sido cancelado o ya se encuentra completado.

5. **Líder de Equipo:**
   - `team_members.is_leader = TRUE` para un `team_id` específico.
   - Si no es organizador de la organización, árbitro del torneo o no se encuentra en otro equipo dentro de ese mismo torneo, puede crear un equipo.
   - Es posible crear solo si el torneo no ha comenzado aún.
   - Puede invitar miembros al equipo (a partir de los usuarios que se hayan unido a esa `organization_id`), a menos que ya haya iniciado, se haya completado o cancelado.
   - Los equipos solo viven dentro de ese torneo en específico.

6. **Jugador/Miembro de Equipo:**
   - Existe una entrada en `team_members` para un `team_id` específico.
   - Participa en el torneo aceptando invitaciones para ser parte de un equipo que participe en el mismo.

### Flujo de Creación de Torneo:

1. Admin (`users`) crea una `organizations`.
2. Admin asigna un `users` como organizador (`organization_members.is_organizer = TRUE`).
3. Organizador (`organization_members`) crea un `tournaments` (opcionalmente dentro de un `events`) para una `activities` existente.
4. Organizador asigna `users` (que sean parte de la `organizations`) como `tournament_referees`.

### Flujo de Participación en Torneo:

1. Usuario (`users`) se une a `organizations` (crea entrada en `organization_members`).
2. Usuario (que no sea árbitro, ni participante/líder de un equipo en ese torneo) crea un `teams` para un `tournaments` (se añade a `team_members` como líder).
3. Líder (`team_members`) envía `team_invitations` a otros `users` de la misma `organizations` (que no estén ya en ese u otro equipo del torneo, sean árbitros del mismo o sean organizadores).
4. Usuario invitado acepta la invitación (se crea entrada en `team_members`, se actualiza `team_invitations.status`).

### Gestión de Partidos:

1. Al iniciar el torneo, la aplicación genera los `matches` (bracket) basado en los `teams` inscritos y sus `seed_score`
2. Un `tournament_referees` registra el resultado (`score_team_a`, `score_team_b`, `best_player_id`) en un `matches`, actualizando su `status` y `winner_id` de manera automática. El `recorded_by_referee_id` se guarda en `matches`.
3. La aplicación actualiza el bracket, propagando el `winner_id` al siguiente `matches` correspondiente.

### Estructura:
```
flaskapp/  
├── __init__.py                  # Entry point  
├── database/                    # Database models and core logic
│   ├── models.py                # All SQLAlchemy models in one place
│   └── ...                      
├── modules/  
│   ├── organization/       # Blueprint: org management  
│   │   ├── routes.py       # URL endpoints (e.g., /login, /profile)  
│   │   ├── forms.py        # Forms & validation  
│   │   ├── service.py      # Business logic (uses database/models.py)  
│   │   ├── dto.py          # Data transfer objects for views (uses database/models.py)  
│   │   └── utils.py        # Others
│   ├── tournament/         # Blueprint: tournaments 
│   │   ├── routes.py  
│   │   ├── forms.py  
│   │   ├── service.py  
│   │   ├── dto.py          
│   │   └── utils.py       
│   └── ...  
├── templates/             # HTML templates  
├── static/                # CSS/JS/images  
requirements.txt  
...
```

## 🚀 Comenzar 

###  Python

1. **Clonar** y crear un entorno virtual para la instalación de dependencias:  
```bash
# Create virtual environment
python -m venv .venv

# Activate the venv
#   For Linux use: source venv/bin/activate
#   If there is an error, change it manually in the bottom right corner (open a .py file first)
.venv\Scripts\activate

# Once the venv if active, install the requirements
.venv\Scripts\pip.exe install -r requirements.txt
```

2. **Crear el archivo de configuración .env**:

O renombrar `.env_example` a `.env` ...

3. **Run run run**:  

```bash
.venv\Scripts\python.exe run.py
```

Ir al sitio:
http://localhost

4. **Testing**:  

####  Modules de prueba

```
flaskapp/  
└── modules/  
    └── activities/  
        ├── service.py       # Lógica a probar  
        └── test/  
            ├── __init__.py 
            ├── test_activities_service.py  # Pruebas unitarias de los servicios usados
            └── factory.py # Datos de prueba (mocks) 
    └── events/  
        ├── service.py       # Lógica a probar  
        └── test/  
            ├── __init__.py 
            ├── test_events_service.py  # Pruebas unitarias de los servicios usados
            └── factory.py # Datos de prueba (mocks)  
```

#### **Correr las pruebas:** Para ello se usa `pytest`

```bash
.venv\Scripts\pip.exe install -r requirements..dev.txt
```

Luego
```bash
pytest
```

###  Ejecutar usando Docker Compose

App+PostgreSQL+pgAdmin

```bash
docker-compose -f ./docker-compose.prod.yml -d up --build
```
# Base de Datos - Modelo Relacional

## Tablas

### 1. Usuarios (users)
Representa a todas las personas que interactúan con la plataforma.

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    profile_picture VARCHAR(255),
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);
```

**Consideraciones:**
- `is_admin`: Perfecto para el administrador global. Los roles de "organizador", "árbitro" y "jugador" son contextuales a organizaciones y torneos, por lo que se manejan en tablas de relación.

### 2. Organizaciones (organizations)
Entidades que gestionan sus propios torneos (ej. universidades, empresas).

```sql
CREATE TABLE organizations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    created_by INTEGER REFERENCES users(id) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);
```

**Consideraciones:**
- `created_by`: Corresponde a alguno de los usuarios administradores (users.is_admin = True)

### 3. Miembros de Organización (organization_members)
Tabla de unión para la relación muchos-a-muchos entre usuarios y organizaciones. Define quién pertenece a qué organización y si es organizador de la misma.

```sql
CREATE TABLE organization_members (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    is_organizer BOOLEAN DEFAULT FALSE,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(organization_id, user_id)
);
```

**Consideraciones:**
- `is_organizer`: Indica si el `user_id` tiene rol de organizador dentro de esa `organization_id`.
- `ON DELETE CASCADE` es útil: si se borra una organización o un usuario, estas membresías se eliminan.

### 4. Actividades (activities)
Tipos de deportes o juegos para los torneos (ej. Fútbol, Ajedrez, LoL).

```sql
CREATE TABLE activities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    min_players_per_team INTEGER NOT NULL DEFAULT 1,
    category_id INTEGER REFERENCES activity_categories(id) ON DELETE SET NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    CONSTRAINT check_min_players_positive 
        CHECK (min_players_per_team > 0)
);
```

```sql
CREATE TABLE activity_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT
);
```

**Consideraciones:**
- `min_players_per_team`: Importante para la validación al iniciar torneos, los equipos sin esa cantidad de jugadores serán descartados. El sistema debe validar.

### 5. Eventos (events)
Un "Evento" podría agrupar varios torneos dentro de una organización (ej. "Copa Mechona 2026").

```sql
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE NOT NULL,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    start_date DATE,
    end_date DATE,
    status_id INTEGER REFERENCES event_statuses(id) NOT NULL,
    created_by INTEGER REFERENCES users(id) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    UNIQUE(organization_id, name),
    UNIQUE(organization_id, id),
    CONSTRAINT check_dates_order
        CHECK (start_date <= end_date)
);
```

```sql
CREATE TABLE event_statuses (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT
);
```

**Consideraciones:**
- La utilización en torneos es opcional. Un torneo podría no estar asociado a algún evento.
- Un evento solo reside dentro de una organización en específico (`organization_id`).

### 6. Torneos (tournaments)
Las competiciones específicas creadas dentro de una organización.

> El torneo opera de la siguiente manera: El sistema organiza torneos de eliminación simple mediante un árbol binario completo, donde primero se calcula el tamaño del bracket (potencia de 2 superior al número de equipos) y se asignan *byes* a los mejores semillas para completarlo. Los equipos se ordenan por *seed_score* (mayor = mejor semilla), y los partidos iniciales enfrentan semillas opuestas (mejor vs. peor restante). Cada **Match** incluye los campos: *level* (ronda, siendo 0 la final), *match_number* (posición en el bracket y en el árbol binario, con 1 la raíz, la final), *team_a* y *team_b*, (ids de equipos, opcionales en *byes*), *score_team_a* y *score_team_b* (marcadores), *winner* (determinado al resolverse el partido), *is_bye* (victoria automática) y *status* (*pending* o *completed*). Si es un *bye*, el ganador avanza automáticamente; al registrarse un resultado (mediante un *trigger* que actualice la siguiente llave), el *winner* se asigna al partido correspondiente en la siguiente ronda, repitiéndose el proceso hasta determinar un campeón en la final.

```sql
CREATE TABLE tournaments (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE RESTRICT,
    event_id INTEGER,
    activity_id INTEGER REFERENCES activities(id) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    max_teams INTEGER NOT NULL,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    prizes TEXT,
    status_id INTEGER REFERENCES tournament_statuses(id) NOT NULL,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    CONSTRAINT check_dates_order 
        CHECK (start_date <= end_date),
    CONSTRAINT check_max_teams_not_negative
        CHECK (max_teams > 0),
    FOREIGN KEY (organization_id, event_id)
        REFERENCES events (organization_id, id) ON DELETE RESTRICT
);
```

```sql
CREATE TABLE tournament_statuses (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT
);
```

**Consideraciones:**
- `event_id` es un FK opcional.
- `end_date` podría ser calculado cuando el status pase a ser `completed` utilizando algún Trigger.

### 7. Árbitros de Torneo (tournament_referees)
Usuarios asignados como árbitros para un torneo específico.

```sql
CREATE TABLE tournament_referees (
    id SERIAL PRIMARY KEY,
    tournament_id INTEGER REFERENCES tournaments(id) ON DELETE CASCADE NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    assigned_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tournament_id, user_id)
);
```

**Consideraciones:**
- Un usuario `user_id` en esta tabla `tournament_referees` para un torneo `tournament_id` no puede ser miembro de un equipo en el mismo torneo `tournament_id`.

### 8. Equipos (teams)
Equipos creados para participar en un torneo específico.

```sql
CREATE TABLE teams (
    id SERIAL PRIMARY KEY,
    tournament_id INTEGER REFERENCES tournaments(id) ON DELETE CASCADE NOT NULL,
    name VARCHAR(100) NOT NULL,
    seed_score INTEGER DEFAULT 0
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    UNIQUE(tournament_id, name),
    CONSTRAINT check_seed_score_not_negative
      CHECK (seed_score >= 0)
);
```

**Consideraciones:**
- El nombre es genérico al comienzo, pero puede ser personalizable por algún líder de equipo.
- No se especifica el líder en esta tabla, eso se especifica al establecer la unión entre equipos y usuarios (`team_members`).
- `seed_score`: Se calculará por la aplicación antes de iniciar el torneo.

### 9. Miembros de Equipo (team_members)
Usuarios que son parte de un equipo en un torneo.

```sql
CREATE TABLE team_members (
    id SERIAL PRIMARY KEY,
    team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    is_leader BOOLEAN DEFAULT FALSE,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(team_id, user_id)
);
```

**Consideraciones:**
- Un `user_id` no puede estar en más de un equipo para el mismo en el mismo torneo: `UNIQUE(team_id, user_id)`
- El `user_id` debe pertenecer a la organización. Revisar `team_id > teams.tournament_id > tournament.organization_id`.
- El `user_id` solo puede ser un usuario perteneciente a la organizador que no sea organizador, ni árbitro del torneo, ni jugador del torneo.
- Debe haber al menos un líder por equipo.

### 10. Partidos (matches)
Los enfrentamientos individuales dentro de un torneo.

```sql
CREATE TABLE matches (
    id SERIAL PRIMARY KEY,
    tournament_id INTEGER REFERENCES tournaments(id) ON DELETE CASCADE NOT NULL,
    level INTEGER NOT NULL, -- Nivel/Ronda en el bracket (ej. 0=final)
    match_number INTEGER NOT NULL, -- Posición única en el árbol del bracket
    team_a_id INTEGER REFERENCES teams(id) ON DELETE SET NULL,
    team_b_id INTEGER REFERENCES teams(id) ON DELETE SET NULL,
    score_team_a INTEGER,
    score_team_b INTEGER,
    winner_id INTEGER REFERENCES teams(id) ON DELETE SET NULL,
    best_player_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    is_bye BOOLEAN DEFAULT FALSE,
    status_id INTEGER REFERENCES match_statuses(id) NOT NULL,
    completed_at TIMESTAMP,
    updated_at TIMESTAMP,
    recorded_by_referee_id INTEGER REFERENCES users(id),
    UNIQUE(tournament_id, match_number),
    CONSTRAINT check_winner_is_participant
        CHECK (winner_id IS NULL OR winner_id = team_a_id OR winner_id = team_b_id),
    CONSTRAINT check_teams_are_distinct
        CHECK (team_a_id IS DISTINCT FROM team_b_id),
    CONSTRAINT check_bye_has_only_team_a
        CHECK (NOT is_bye OR (team_a_id IS NOT NULL AND team_b_id IS NULL)),
    CONSTRAINT check_scores_consistency
        CHECK (
            (score_team_a IS NULL AND score_team_b IS NULL) OR
            (score_team_a IS NOT NULL AND score_team_b IS NOT NULL AND score_team_a <> score_team_b)
        )
);
```

```sql
CREATE TABLE match_statuses (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT
);
```

**Consideraciones:**
- `level` y `match_number` definen la estructura del bracket. Al crear, siempre se estructurará un árbol binario completo.
- `best_player_id`: Debería ser un `user_id` que sea miembro de `team_a_id` o `team_b_id` participando en `tournament_id`.
- `recorded_by_referee_id`: Almacena el `user_id` del árbitro que ingresó o modificó por última vez el resultado. Este usuario debe estar `tournament_referees` (en `tournament_referees.user_id` para esse `tournament.tournament_id`).
- EL árbitro podrá modificar resultados de ciertas partida. La lógica de "si la siguiente llave no ha sido jugada aún" para editar resultados es de aplicación, usando `status` y `completed_at` del Match sucesor.
- Al inicial el torneo el sistema crea todos las partidas necesarias (Match), por lo que existirán muchas partidas que no tendrán equipos (`team_a_id` o `team_b_id`) asociados de momento. Un ejemplo, la final.

### 11. Invitaciones a Equipos (team_invitations)
Para que los líderes de equipo inviten a otros usuarios.

```sql
CREATE TABLE team_invitations (
    id SERIAL PRIMARY KEY,
    team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE NOT NULL,
    invited_by_user_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    invited_user_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    status_id INTEGER REFERENCES team_invitations_statuses(id) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    UNIQUE(team_id, invited_user_id)
);
```

```sql
CREATE TABLE team_invitations_statuses (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT
);
```

**Consideraciones:**
- Al aceptar, se crea un registro en `team_members` y se cancelan otras invitaciones pendientes para ese `invited_user_id` en el mismo torneo (lógica de aplicación).
- No es posible invitar a ese jugador a equipos en ese torneo si ya es parte de ese mismo equipo u otro en ese mismo torneo, es árbitro de ese torneo, es organizador de la organización donde reside el torneo o ya tiene un `team_invitations` pendiente para ese equipo en ese mismo torneo.

### 12. Notificaciones (notifications)
Para informar a los usuarios sobre eventos relevantes.

```sql
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    title VARCHAR(150) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    type_id INTEGER REFERENCES notification_types(id) NOT NULL, -- ej: "Se ha iniciado el torneo"
    related_entity_type_id INTEGER REFERENCES related_entity_types(id) NOT NULL, -- ej: tipo: tournament
    related_entity_id INTEGER NOT NULL, -- ej: el id del tournament en cuestión
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

```sql
CREATE TABLE notification_types (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT
);
```

```sql
CREATE TABLE related_entity_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);
```

**Consideraciones:**
- `type_id` puede ayudar a la UI a manejar diferentes tipos de notificaciones con iconos o acciones específicas.
- `related_entity_type` y `related_entity_id` son útiles para enlazar la notificación a la entidad que la originó. Una organización, un torneo o un equipo (`related_entity_type_id`) pueden generar diferentes tipos de notificaciones.

## Funciones

### Función de automatización del campo updated_at

```sql
CREATE OR REPLACE FUNCTION trigger_set_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

### Función para propagar ganadores y manejar estados

```sql
CREATE OR REPLACE FUNCTION handle_match_result()
RETURNS TRIGGER AS $$
DECLARE
    completed_status_id INTEGER;
    next_match RECORD;
    bye_team_id INTEGER;
BEGIN
    -- Obtener ID del estado 'completed'
    SELECT id INTO completed_status_id 
    FROM match_statuses 
    WHERE code = 'completed';
    
    -- 1. Automáticamente marcar como completado si se ingresan ambos scores
    IF NEW.score_team_a IS NOT NULL 
       AND NEW.score_team_b IS NOT NULL 
       AND OLD.status_id <> completed_status_id 
    THEN
        NEW.status_id := completed_status_id;
        NEW.completed_at := NOW();
    END IF;
    
    -- 2. Determinar ganador automáticamente al completarse
    IF NEW.status_id = completed_status_id THEN
        -- Caso Bye: ganador automático es team_a
        IF NEW.is_bye THEN
            NEW.winner_id := NEW.team_a_id;
        -- Partido normal: calcular ganador por score
        ELSIF NEW.score_team_a > NEW.score_team_b THEN
            NEW.winner_id := NEW.team_a_id;
        ELSIF NEW.score_team_b > NEW.score_team_a THEN
            NEW.winner_id := NEW.team_b_id;
        -- Empate (requiere manejo adicional)
        ELSE
            NEW.winner_id := NULL; -- La aplicación debe manejar desempates
        END IF;
    END IF;
    
    -- 3. Propagación automática al siguiente match (excepto final)
    IF NEW.status_id = completed_status_id 
       AND NEW.winner_id IS NOT NULL 
       AND NEW.level > 0 -- Excluir final (level 0)
    THEN
        -- Calcular posición del siguiente match
        next_match.match_number := CEIL(NEW.match_number / 2.0);
        next_match.level := NEW.level - 1;
        
        -- Determinar posición en el siguiente match
        IF NEW.match_number % 2 = 0 THEN
            -- Posición par -> team_a del siguiente match
            UPDATE matches
            SET team_a_id = NEW.winner_id,
                updated_at = NOW()
            WHERE tournament_id = NEW.tournament_id
              AND level = next_match.level
              AND match_number = next_match.match_number;
        ELSE
            -- Posición impar -> team_b del siguiente match
            UPDATE matches
            SET team_b_id = NEW.winner_id,
                updated_at = NOW()
            WHERE tournament_id = NEW.tournament_id
              AND level = next_match.level
              AND match_number = next_match.match_number;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

### Función para manejar Byes al crear partidos

```sql
CREATE OR REPLACE FUNCTION handle_new_match()
RETURNS TRIGGER AS $$
BEGIN
    -- Auto-completar Byes al crear partidos
    IF NEW.is_bye THEN
        NEW.status_id := (SELECT id FROM match_statuses WHERE code = 'completed');
        NEW.winner_id := NEW.team_a_id;
        NEW.completed_at := NOW();
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

### Función de propagación inmediata para Byes

```sql
CREATE OR REPLACE FUNCTION propagate_bye_winner()
RETURNS TRIGGER AS $$
DECLARE
    next_match RECORD;
BEGIN
    IF NEW.is_bye AND NEW.winner_id IS NOT NULL AND NEW.level > 0 THEN
        -- Calcular siguiente match
        next_match.match_number := CEIL(NEW.match_number / 2.0);
        next_match.level := NEW.level - 1;
        
        -- Propagación inmediata
        IF NEW.match_number % 2 = 0 THEN
            UPDATE matches
            SET team_a_id = NEW.winner_id
            WHERE tournament_id = NEW.tournament_id
              AND level = next_match.level
              AND match_number = next_match.match_number;
        ELSE
            UPDATE matches
            SET team_b_id = NEW.winner_id
            WHERE tournament_id = NEW.tournament_id
              AND level = next_match.level
              AND match_number = next_match.match_number;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

### Función para bloquear edición de matches Bye

```sql
CREATE OR REPLACE FUNCTION validate_bye_match()
RETURNS TRIGGER AS $$
DECLARE
    completed_status_id INTEGER;
BEGIN
    -- Obtener ID del estado 'completed' una sola vez
    SELECT id INTO completed_status_id 
    FROM match_statuses 
    WHERE code = 'completed';
    
    -- Si es Bye, verificar que no se esté modificando
    IF OLD.is_bye THEN
        IF (
            -- Cambios prohibidos:
            NEW.team_a_id <> OLD.team_a_id OR
            NEW.team_b_id IS NOT NULL OR  -- Bye solo debe tener team_a
            NEW.is_bye = FALSE OR
            NEW.status_id <> completed_status_id OR
            NEW.winner_id <> OLD.team_a_id OR
            (NEW.score_team_a IS NOT NULL OR NEW.score_team_b IS NOT NULL)
        ) THEN
            RAISE EXCEPTION 
                'No se puede modificar un Match Bye. Intento de cambio en Match ID: %', 
                OLD.id;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

## Triggers

### Trigger de automatización del campo updated_at para tablas que lo soportan

```sql
DO $$
DECLARE
    tabla text;
BEGIN
    FOR tabla IN 
        SELECT table_name 
        FROM information_schema.columns 
        WHERE column_name = 'updated_at' 
        AND table_name IN (
            'users', 'organizations', 'activities', 
            'events', 'tournaments', 'teams', 
            'matches', 'team_invitations'
        )
    LOOP
        EXECUTE format('
            CREATE TRIGGER set_timestamp_%s
            BEFORE UPDATE ON %I
            FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();
        ', tabla, tabla);
    END LOOP;
END$$;
```

### Trigger para propagar ganadores y manejar estados

```sql
CREATE TRIGGER match_result_trigger
    BEFORE INSERT OR UPDATE ON matches
    FOR EACH ROW EXECUTE FUNCTION handle_match_result();
```

### Trigger para manejar Byes al crear partidos

```sql
CREATE TRIGGER new_match_trigger
    BEFORE INSERT ON matches
    FOR EACH ROW EXECUTE FUNCTION handle_new_match();
```

### Trigger de propagación inmediata para Byes

```sql
CREATE TRIGGER bye_propagation_trigger
AFTER INSERT ON matches
FOR EACH ROW EXECUTE FUNCTION propagate_bye_winner();
```

### Trigger para bloquear edición de matches Bye

```sql
CREATE TRIGGER lock_bye_matches
BEFORE UPDATE ON matches
FOR EACH ROW EXECUTE FUNCTION validate_bye_match();
```

## (opcional) Índices

```sql
-- Índices para tablas principales
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_organizations_name ON organizations(name);
CREATE INDEX idx_activities_name ON activities(name);

-- Índices para relaciones frecuentes
CREATE INDEX idx_organization_members_user ON organization_members(user_id);
CREATE INDEX idx_organization_members_org ON organization_members(organization_id);
CREATE INDEX idx_tournament_referees_user ON tournament_referees(user_id);
CREATE INDEX idx_team_members_user ON team_members(user_id);
CREATE INDEX idx_team_members_team ON team_members(team_id);

-- Índices para búsquedas en torneos y eventos
CREATE INDEX idx_tournaments_organization ON tournaments(organization_id);
CREATE INDEX idx_tournaments_activity ON tournaments(activity_id);
CREATE INDEX idx_tournaments_status ON tournaments(status_id);
CREATE INDEX idx_events_organization ON events(organization_id);
CREATE INDEX idx_events_status ON events(status_id);

-- Índices para el sistema de matches (bracket)
CREATE INDEX idx_matches_tournament_level ON matches(tournament_id, level);
CREATE INDEX idx_matches_tournament_status ON matches(tournament_id, status_id);
CREATE INDEX idx_matches_team_a ON matches(team_a_id) WHERE team_a_id IS NOT NULL;
CREATE INDEX idx_matches_team_b ON matches(team_b_id) WHERE team_b_id IS NOT NULL;
CREATE INDEX idx_matches_winner ON matches(winner_id) WHERE winner_id IS NOT NULL;

-- Índices para notificaciones
CREATE INDEX idx_notifications_user ON notifications(user_id);
CREATE INDEX idx_notifications_read ON notifications(user_id, is_read) WHERE is_read = FALSE;
CREATE INDEX idx_notifications_entity ON notifications(related_entity_type_id, related_entity_id);

-- Índices para invitaciones
CREATE INDEX idx_team_invitations_user ON team_invitations(invited_user_id);
CREATE INDEX idx_team_invitations_status ON team_invitations(status_id);
```

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
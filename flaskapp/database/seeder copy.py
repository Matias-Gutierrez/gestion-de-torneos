# flaskapp/database/seeder.py

import random
from datetime import datetime, timedelta
import uuid
from faker import Faker
from sqlalchemy.exc import IntegrityError

from flaskapp import db
from flaskapp.database.models import (
    User, Organization, OrganizationMember, Activity, ActivityCategory,
    Event, Tournament, Team, TeamMember, TournamentReferee, Match,
    EventStatus, TournamentStatus, MatchStatus, TeamInvitationStatus,
    NotificationType, RelatedEntityType
)

# Configuración inicial
fake = Faker('es_CL')
NUM_USERS = 200 # Número total de usuarios a crear
# Para pruebas, se crean 5 administradores y el resto son usuarios normales
NUM_ORGANIZATIONS = 2
NUM_ACTIVITIES = 5
PASSWORD = "password1" # Contraseña común para desarrollo

def seed_database(app):
    """
    Función principal para poblar la base de datos con datos de prueba.
    Utiliza el ORM de SQLAlchemy para crear objetos y manejar relaciones.
    """
    with app.app_context():
        # 1. Verificar si la base de datos ya tiene datos
        if db.session.query(User).first():
            print("Saltando el proceso de seeding: La base de datos ya contiene usuarios.")
            return

        print("Iniciando el proceso de seeding...")
        try:
            # 2. Crear datos maestros (tablas de estado, tipos, categorías)
            print("Creando datos maestros (estados, tipos, etc.)...")
            seed_master_data()

            # 3. Crear entidades principales en orden de dependencia
            print(f"Generando {NUM_ACTIVITIES} actividades...")
            activities = create_activities(NUM_ACTIVITIES)

            print(f"Generando {NUM_USERS} usuarios...")
            users, admins = create_users(NUM_USERS)

            print(f"Generando {NUM_ORGANIZATIONS} organizaciones...")
            organizations = create_organizations(NUM_ORGANIZATIONS, admins)
            
            print("Asignando miembros a las organizaciones...")
            organization_members = assign_members_to_organizations(organizations, users)

            print("Generando eventos y torneos...")
            create_events_and_tournaments(organizations, activities, organization_members)

            # 4. Confirmar todos los cambios en la base de datos
            db.session.commit()
            print("\n¡Seeding completado exitosamente! ✅")

        except IntegrityError as e:
            db.session.rollback()
            print(f"\nError de integridad durante el seeding: {e}")
            print("Se ha revertido la transacción. La base de datos está en su estado original.")
        except Exception as e:
            db.session.rollback()
            print(f"\nOcurrió un error inesperado durante el seeding: {e}")
            print("Se ha revertido la transacción.")

def seed_master_data():
    """Crea los registros en las tablas de estado y tipo."""
    statuses_data = {
        EventStatus: [
            {'code': 'PLANNED', 'description': 'Evento planificado, aún no ha comenzado'},
            {'code': 'IN_PROGRESS', 'description': 'Evento en curso'},
            {'code': 'COMPLETED', 'description': 'Evento finalizado'},
            {'code': 'CANCELLED', 'description': 'Evento cancelado'},
        ],
        TournamentStatus: [
            {'code': 'REGISTRATION_OPEN', 'description': 'Inscripciones abiertas'},
            {'code': 'IN_PROGRESS', 'description': 'Torneo en curso'},
            {'code': 'COMPLETED', 'description': 'Torneo finalizado'},
            {'code': 'CANCELLED', 'description': 'Torneo cancelado'},
        ],
        MatchStatus: [
            {'code': 'PENDING', 'description': 'Partido pendiente'},
            {'code': 'COMPLETED', 'description': 'Partido finalizado'},
            {'code': 'CANCELLED', 'description': 'Partido cancelado'}
        ],
        TeamInvitationStatus: [
            {'code': 'PENDING', 'description': 'Invitación pendiente de respuesta'},
            {'code': 'ACCEPTED', 'description': 'Invitación aceptada'},
            {'code': 'REJECTED', 'description': 'Invitación rechazada'},
        ],
        NotificationType: [
            {'code': 'TEAM_INVITE', 'description': 'Invitación a equipo'},
            {'code': 'TOURNAMENT_START', 'description': 'El torneo ha iniciado'}
        ],
        RelatedEntityType: [
            {'name': 'TOURNAMENT'}
        ],
        ActivityCategory: [
            {'name': 'eSports'},
            {'name': 'Deportes Tradicionales'}
        ]
    }

    for model, data_list in statuses_data.items():
        for data in data_list:
            instance = model(**data)
            db.session.add(instance)
    
    db.session.flush()

def create_users(num_users):
    """Genera usuarios y los divide en administradores y usuarios normales."""
    
    users = []
    admins = []
    
    for i in range(1, num_users + 1):
        is_admin = i <= 5 # Los primeros 5 son administradores

        # Nombre y foto de perfil según el género
        if i % 2 == 0:
            f_name = fake.name_female()
            f_profile_pic = f"https://randomuser.me/api/portraits/women/{i % 100}.jpg"
        else:
            f_name = fake.name_male()
            f_profile_pic = f"https://randomuser.me/api/portraits/men/{i % 100}.jpg"
            
        user = User(
            name=f_name,
            email=f"usuario{i}@{fake.domain_name()}",
            password=PASSWORD,
            profile_picture=f_profile_pic,
            is_admin=is_admin,
            created_at=fake.date_time_between(start_date='-2y', end_date='now')
        )
        db.session.add(user)
        users.append(user)
        if is_admin:
            admins.append(user)
    
    db.session.flush()
    return users, admins

def create_activities(num_activities):
    """Genera actividades de ejemplo."""
    esports_category = db.session.query(ActivityCategory).filter_by(name='eSports').one()
    
    activity_names = ['League of Legends', 'Valorant', 'Counter-Strike 2', 'EA FC 25', 'Dota 2', 'Overwatch 2']
    min_players = {'League of Legends': 5, 'Valorant': 5, 'Counter-Strike 2': 5, 'EA FC 25': 1, 'Dota 2': 5, 'Overwatch 2': 5}
    
    activities = []
    for name in random.sample(activity_names, num_activities):
        activity = Activity(
            name=name,
            description=fake.paragraph(nb_sentences=2),
            min_players_per_team=min_players.get(name, 1),
            category=esports_category,
            is_active=True
        )
        db.session.add(activity)
        activities.append(activity)
        
    db.session.flush()
    return activities

def create_organizations(num_orgs, admins):
    """Genera organizaciones, asignando un administrador como creador."""
    orgs = []
    org_names = set()
    while len(org_names) < num_orgs:
        org_names.add(f"{fake.company()} eSports")

    for name in org_names:
        org = Organization(
            name=name,
            description=fake.paragraph(nb_sentences=3),
            creator=random.choice(admins),
            created_at=fake.date_time_between(start_date='-1y', end_date='-6m')
        )
        db.session.add(org)
        orgs.append(org)
        
    db.session.flush()
    return orgs

def assign_members_to_organizations(organizations, users):
    """Asigna usuarios a organizaciones, definiendo roles."""
    all_memberships = []
    for org in organizations:
        # Asignar entre 75 y 300 miembros
        potential_members = [u for u in users if u.id != org.creator.id]
        num_members = random.randint(75, 300)
        members_to_add = random.sample(potential_members, min(num_members, len(potential_members)))
        
        first_is_organizer = True
        for user in members_to_add:
            if first_is_organizer: 
                is_organizer = True
                first_is_organizer = False
            else:
                is_organizer = random.random() < 0.1
            membership = OrganizationMember(
                organization=org,
                user=user,
                is_organizer=is_organizer,
                joined_at=fake.date_time_between_dates(datetime_start=org.created_at)
            )
            db.session.add(membership)
            all_memberships.append(membership)
            
    db.session.flush()
    return all_memberships

def create_events_and_tournaments(organizations, activities, all_memberships):
    """Crea eventos y torneos para cada organización."""
    # Obtener estados necesarios
    event_status_planned = db.session.query(EventStatus).filter_by(code='PLANNED').one()
    tourney_status_reg_open = db.session.query(TournamentStatus).filter_by(code='REGISTRATION_OPEN').one()
    tourney_status_completed = db.session.query(TournamentStatus).filter_by(code='COMPLETED').one()
    tourney_status_cancelled = db.session.query(TournamentStatus).filter_by(code='CANCELLED').one()

    # Mapear organización a sus miembros
    org_member_map = {}
    for m in all_memberships:
        if m.organization_id not in org_member_map:
            org_member_map[m.organization_id] = []
        org_member_map[m.organization_id].append(m)

    for org in organizations:
        print(f"Procesando organización: {org.name} (ID: {org.id})")
        org_members = org_member_map.get(org.id, [])
        organizers = [m.user for m in org_members if m.is_organizer]
        if not organizers:
            continue

        # Crear 1-3 eventos por organización
        used_event_names = set()
        for _ in range(random.randint(1, 3)):
            while True:
                event_name = f"Evento {fake.word().capitalize()} de {fake.historic_people_street_name()}"
                if event_name not in used_event_names:
                    used_event_names.add(event_name)
                    break
            try:
                start = fake.date_time_this_year(after_now=True)
                event = Event(
                    organization=org,
                    name=event_name,
                    description=fake.sentence(),
                    start_date=start,
                    end_date=start + timedelta(days=random.randint(2, 7)),
                    status=event_status_planned,
                    creator=random.choice(organizers)
                )
                db.session.add(event)
            except IntegrityError as e:
                print(f"Error al crear evento: {e}. Saltando este evento.")
                continue
        
        db.session.flush()

        # Crear diferentes tipos de torneos
        create_tournament_variants(org, activities, organizers, 
                                 tourney_status_reg_open, tourney_status_completed, 
                                 tourney_status_cancelled, org_members)
    
    db.session.flush()

def get_potential_players_for_tournament(tournament):
    """
    Obtiene una lista de usuarios elegibles para participar como jugadores en un torneo.
    
    Aplica las siguientes reglas:
    - Deben ser miembros de la organización del torneo.
    - NO pueden ser administradores de la plataforma (is_admin).
    - NO pueden ser organizadores de la organización.
    - NO pueden ser árbitros asignados a ESE torneo.
    """
    
    # Obtener IDs de usuarios que ya son árbitros en este torneo
    referee_user_ids = {ref.user_id for ref in tournament.referees}
    
    potential_players = []
    # Iteramos sobre los miembros de la organización a la que pertenece el torneo
    for member in tournament.organization.members:
        # Aplicamos todas las condiciones de elegibilidad
        if (not member.user.is_admin and
                not member.is_organizer and
                member.user_id not in referee_user_ids):
            potential_players.append(member.user)
            
    return potential_players

def create_tournament_variants(org, activities, organizers, status_open, status_completed, status_cancelled, org_members):
    """Crea diferentes variantes de torneos según los requerimientos."""
    print(f"  Creando torneos para la organización: {org.name} (ID: {org.id})")
    
    # 1. Torneos COMPLETADOS (2 por organización)
    for _ in range(random.randint(0, 1)):
        create_completed_tournament(org, activities, organizers, status_completed, org_members)
    
    # 2. Torneos PENDIENTES (2-3 por organización)
    for _ in range(random.randint(2, 3)):
        create_pending_tournament(org, activities, organizers, status_open, org_members)
    
    # 3. Torneos CANCELADOS (0-2 por organización)
    for _ in range(random.randint(0, 1)):
        create_cancelled_tournament(org, activities, organizers, status_cancelled, org_members)

def create_completed_tournament(org, activities, organizers, status_completed, org_members):
    """Crea un torneo completado con bracket desde semifinales (4 equipos)."""
    print(f"    Creando torneo COMPLETADO para la organización: {org.name} (ID: {org.id})")
    
    # Fechas pasadas
    end_date = fake.date_time_between(start_date='-3m', end_date='-1w')
    start_date = end_date - timedelta(days=random.randint(1, 3))
    
    # Evento asociado (opcional)
    linked_event = random.choice(org.events) if org.events and random.random() < 0.7 else None
    
    tournament = Tournament(
        organization=org,
        event=linked_event,
        activity=random.choice(activities),
        name=f"Copa {fake.word().capitalize()} COMPLETED",
        description=fake.paragraph(nb_sentences=3),
        max_teams=4,  # Exactamente 4 equipos para semifinales
        start_date=start_date,
        end_date=end_date,
        status=status_completed,
        creator=random.choice(organizers),
        prizes=f"1er lugar: {fake.currency_name()}, 2do lugar: {fake.currency_name()}"
    )
    db.session.add(tournament)
    db.session.flush()

    # Crear árbitros
    create_referees_for_tournament(tournament, org_members, random.choice(organizers))
    db.session.flush()

    potential_players = get_potential_players_for_tournament(tournament)
    
    # Crear exactamente 4 equipos
    teams = create_teams_for_tournament(tournament, potential_players, 4, prefix="Team")  

    # Si no se pudieron crear los 4 equipos, no se puede generar el bracket.
    if len(teams) < 4:
        print(f"    AVISO: No se pudieron crear los 4 equipos necesarios para el bracket completado. Se crearon {len(teams)}. Saltando creación de bracket.")
        return  
    
    # Crear bracket completo (semifinales + final)
    create_completed_bracket(tournament, teams, end_date)

def generate_name(generators): 
    num_parts = random.randint(1, 2)
    parts = random.sample(generators, num_parts)
    name = ' '.join(gen() for gen in parts)
    number = random.randint(1, 999)
    return f"{name} {number}"

def create_teams_for_tournament(tournament, potential_players, num_teams, prefix=""):
    """
    Crea equipos para un torneo a partir de una lista de jugadores elegibles.
    Garantiza que un jugador solo pertenezca a un equipo por torneo.
    """   
    print(f"    Creando {num_teams} equipos para el torneo: {tournament.name} (ID: {tournament.id})")
    teams = []

    # Hacemos una copia de la lista para poder modificarla de forma segura
    available_players = list(potential_players)
    
    # Obtener nombres ya usados en este torneo
    existing_team_names = {t.name for t in tournament.teams}
    
    # Fuentes de nombres mejoradas
    prefix = f"{prefix} " if prefix else ""
    name_generators = [
        lambda: f"{prefix}{fake.city()}",
        lambda: f"{fake.color_name()} {prefix.strip()}",
        lambda: f"{prefix}{fake.job()}",
        lambda: f"{fake.street_suffix()} {prefix.strip()}",
        lambda: f"{prefix}{random.choice(['United', 'FC', 'Gaming', 'Esports', 'Pro'])}",
    ]
        
    for i in range(num_teams):
        if len(potential_players) < tournament.activity.min_players_per_team:
            print(f"      No hay suficientes jugadores (necesarios: {tournament.activity.min_players_per_team})")
            break

        # Generar nombre único para este torneo
        team_name = None
        for _ in range(50):  # 50 intentos con diferentes estrategias
            min_required_players = tournament.activity.min_players_per_team
            base_name = generate_name(name_generators)
            
            # Variaciones para aumentar unicidad
            variations = [
                base_name,
                f"{base_name} {random.randint(1, 999)}"
            ]
            
            for candidate in variations:
                if candidate not in existing_team_names:
                    team_name = candidate
                    existing_team_names.add(team_name)
                    break
            if team_name:
                break
        else:
            # Fallback definitivo garantizado
            team_name = f"{prefix} {uuid.uuid4().hex[:8]}"
        
        # Crear equipo
        print(f"      Creando equipo: {team_name} (ID: {i+1})")
        try:
            team = Team(
                tournament=tournament,
                name=team_name,
                seed_score=random.randint(2, 7)*5*tournament.activity.min_players_per_team,
            )
            db.session.add(team)
            
            # Seleccionar y remover al líder de la lista de disponibles
            team_leader = random.choice(available_players)
            available_players.remove(team_leader)
            
            leader_member = TeamMember(team=team, user=team_leader, is_leader=True)
            db.session.add(leader_member)
            
            # Seleccionar y remover al resto de miembros
            # Nos aseguramos que haya suficientes jugadores restantes
            num_other_members = min_required_players - 1
            if len(available_players) >= num_other_members:
                other_members = random.sample(available_players, num_other_members)
                for member in other_members:
                    db.session.add(TeamMember(team=team, user=member, is_leader=False))
                    available_players.remove(member) # Crucial: remover para no volver a usarlo
            
            db.session.flush() # Commit a nivel de equipo para asegurar consistencia
            teams.append(team)
            
        except IntegrityError as e:
            db.session.rollback()
            print(f"      Error de integridad al crear equipo: {e}. Reintentando...")
            # Devolver los jugadores a la lista si la transacción falla
            # (Aunque con nombres únicos y jugadores únicos, es menos probable)
            continue
    
    return teams

def create_completed_bracket(tournament, teams, end_date):
    """Crea el bracket completo de un torneo terminado (semifinales + final)."""
    print(f"    Creando bracket COMPLETED para el torneo: {tournament.name} (ID: {tournament.id})")
    match_status_completed = db.session.query(MatchStatus).filter_by(code='COMPLETED').one()
    
    # Ordenar equipos por seed_score (mejor seed primero)
    teams.sort(key=lambda t: t.seed_score, reverse=True)
    
    # SEMIFINALES (Level 1)
    # Semifinal 1: Mejor seed vs 4to seed
    team_a = teams[0]
    team_b = teams[3]
    score_a = random.randint(1, 3)
    score_b = random.randint(1, 3)
    
    # Asegurar que haya un ganador claro
    if score_a == score_b:
        score_a += 1
    
    semi1 = Match(
        tournament_id=tournament.id,
        level=1,
        match_number=2,
        team_a_id=team_a.id,
        team_b_id=team_b.id,
        score_team_a=score_a,
        score_team_b=score_b,
        winner_id=team_a.id if score_a > score_b else team_b.id,
        status_id=match_status_completed.id,
        completed_at=end_date - timedelta(days=1))
    
    # Seleccionar mejor jugador del equipo ganador
    winning_team = team_a if score_a > score_b else team_b
    winning_team_members = [m.user_id for m in winning_team.members]
    semi1.best_player_id = random.choice(winning_team_members) if winning_team_members else None
    
    db.session.add(semi1)
    
    # Semifinal 2: 2do seed vs 3er seed
    team_c = teams[1]
    team_d = teams[2]
    score_c = random.randint(1, 3)
    score_d = random.randint(1, 3)
    
    if score_c == score_d:
        score_c += 1
    
    semi2 = Match(
        tournament_id=tournament.id,
        level=1,
        match_number=3,
        team_a_id=team_c.id,
        team_b_id=team_d.id,
        score_team_a=score_c,
        score_team_b=score_d,
        winner_id=team_c.id if score_c > score_d else team_d.id,
        status_id=match_status_completed.id,
        completed_at=end_date - timedelta(days=1))
    
    winning_team2 = team_c if score_c > score_d else team_d
    winning_team2_members = [m.user_id for m in winning_team2.members]
    semi2.best_player_id = random.choice(winning_team2_members) if winning_team2_members else None
    
    db.session.add(semi2)

    db.session.flush()
    
    # FINAL (Level 0)
    final_team_a = db.session.get(Team, semi1.winner_id)
    final_team_b = db.session.get(Team, semi2.winner_id)
    final_score_a = random.randint(1, 3)
    final_score_b = random.randint(1, 3)
    
    if final_score_a == final_score_b:
        final_score_a += 1

    final = Match(
        tournament_id=tournament.id,
        level=0,
        match_number=1,
        team_a_id=final_team_a.id,
        team_b_id=final_team_b.id,
        score_team_a=final_score_a,
        score_team_b=final_score_b,
        winner_id=final_team_a.id if final_score_a > final_score_b else final_team_b.id,
        status_id=match_status_completed.id,
        completed_at=end_date)
    
    final_winner = final_team_a if final_score_a > final_score_b else final_team_b
    final_winner_members = [m.user_id for m in final_winner.members]
    final.best_player_id = random.choice(final_winner_members) if final_winner_members else None
    
    db.session.add(final)

def create_pending_tournament(org, activities, organizers, status_open, org_members):
    """Crea un torneo pendiente con fechas futuras."""
    print(f"    Creando torneo PENDIENTE para la organización: {org.name} (ID: {org.id})")
    
    # Fechas futuras (1-8 semanas a partir de hoy)
    start_date = fake.date_time_between(start_date='+1w', end_date='+8w')
    end_date = start_date + timedelta(days=random.randint(1, 14))
    
    linked_event = random.choice(org.events) if org.events and random.random() < 0.7 else None
    
    tournament = Tournament(
        organization=org,
        event=linked_event,
        activity=random.choice(activities),
        name=f"Copa {fake.word().capitalize()} REGISTRATION_OPEN",
        description=fake.paragraph(nb_sentences=4),
        max_teams=random.choice([4, 8, 16]),
        start_date=start_date,
        end_date=end_date,
        status=status_open,
        creator=random.choice(organizers)
    )
    db.session.add(tournament)
    db.session.flush()
    
    # Crear participantes (equipos incompletos y árbitros)
    create_tournament_participants(tournament, org_members, random.choice(organizers))

def create_cancelled_tournament(org, activities, organizers, status_cancelled, org_members):
    """Crea un torneo cancelado con fechas pasadas."""
    print(f"    Creando torneo CANCELLED para la organización: {org.name} (ID: {org.id})")
    
    # Fechas pasadas (hace 1-6 meses)
    start_date = fake.date_time_between(start_date='-6m', end_date='-1m')
    end_date = start_date + timedelta(days=random.randint(1, 14))
    
    linked_event = random.choice(org.events) if org.events and random.random() < 0.7 else None
    
    tournament = Tournament(
        organization=org,
        event=linked_event,
        activity=random.choice(activities),
        name=f"Copa {fake.word().capitalize()} CANCELLED",
        description=fake.paragraph(nb_sentences=3),
        max_teams=random.choice([4, 8, 16]),
        start_date=start_date,
        end_date=end_date,
        status=status_cancelled,
        creator=random.choice(organizers)
    )
    db.session.add(tournament)
    db.session.flush()
    
    # Crear algunos participantes (pocos equipos, simular inscripciones incompletas)
    create_limited_tournament_participants(tournament, org_members, random.choice(organizers))

def create_limited_tournament_participants(tournament, org_members, organizer):
    """Crea participantes limitados para torneos cancelados usando jugadores elegibles."""
    
    # 1. Solo 1-2 árbitros
    create_referees_for_tournament(tournament, org_members, organizer, count_range=(1,2))
    db.session.flush()

    # 2. Obtener jugadores elegibles
    potential_players = get_potential_players_for_tournament(tournament)
    
    # 3. Solo 1-3 equipos (inscripciones incompletas)
    if potential_players:
        num_teams_to_create = random.randint(1, 3)
        create_teams_for_tournament(tournament, potential_players, num_teams_to_create, prefix="Team Cancelado")


def create_referees_for_tournament(tournament, org_members, organizer, count_range=(2, 4)):
    """
    Crea árbitros para un torneo a partir de una lista de miembros de la organización.
    """

    # 1. Filtrar los MIEMBROS de la organización que son elegibles para ser árbitros.
    #    Un árbitro no puede ser un administrador de plataforma ni un organizador.
    eligible_members = [
        m for m in org_members
        if not m.user.is_admin and not m.is_organizer
    ]

    # 2. De la lista de miembros elegibles, obtener los OBJETOS User.
    potential_referee_users = [m.user for m in eligible_members]
    
    # 3. Determinar cuántos árbitros crear y seleccionarlos.
    num_referees_to_create = random.randint(*count_range)
    # No intentar tomar más árbitros de los que hay disponibles.
    num_referees_to_create = min(num_referees_to_create, len(potential_referee_users))

    if num_referees_to_create > 0:
        # Seleccionar los usuarios que serán árbitros de la lista de usuarios elegibles.
        selected_users = random.sample(potential_referee_users, num_referees_to_create)
        
        for user_ref in selected_users:
            # Crear el registro en la tabla TournamentReferee.
            referee = TournamentReferee(
                tournament=tournament,
                user=user_ref,  # Asignamos el objeto User.
                assigned_by_user=organizer
            )
            db.session.add(referee)

def create_tournament_participants(tournament, org_members, organizer):
    """Puebla un torneo pendiente con árbitros y equipos usando jugadores elegibles."""
    
    # 1. Asignar árbitros (sin cambios en esta parte)
    create_referees_for_tournament(tournament, org_members, organizer)
    db.session.flush()

    # 2. Obtener jugadores elegibles DESPUÉS de asignar árbitros
    potential_players = get_potential_players_for_tournament(tournament)
    
    # 3. Crear equipos
    # Inscribir entre 2 y (max_teams - 1) equipos, si hay jugadores
    if potential_players and tournament.max_teams > 2:
        num_teams_to_create = random.randint(2, max(2, tournament.max_teams - 1))
        create_teams_for_tournament(tournament, potential_players, num_teams_to_create)
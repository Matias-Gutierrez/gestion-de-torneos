
from datetime import datetime
from unittest.mock import MagicMock
from flaskapp.database.models import Activity, ActivityCategory, Tournament, User

def mock_activity():
    return Activity(
            id=1,
            name="LoL",
            description="Para llorar un rato",
            min_players_per_team=11,
            category_id=3,
            is_active=True,
            created_by=42,
            created_at=datetime(2023, 5, 15, 10, 30),
            updated_at=datetime(2023, 5, 20, 14, 15)
        )

def mock_user():
    # Relación con el creador (User)
    return User(
        id=42,
        name="Test User",
        email="test.user@example.com",
        password="password",
        is_admin=False,
        created_at=datetime(2023, 1, 1),
        updated_at=datetime(2023, 5, 1)
    )

def mock_category():
    # Relación con la categoría (ActivityCategory)
    return ActivityCategory(
        id=3,
        name="eSports",
        description="eSports populares"
    )

def mock_organization():
    organization = MagicMock()
    organization.name = "Organización de Prueba"
    organization.id = 1
    return organization

def mock_tournament():
    # Relación con torneos (lista de Tournament)
    return [
        Tournament(
            id=101,
            organization=mock_organization(),
            organization_id=1,
            activity_id=1,
            name="Torneo de Fútbol Primavera 2023",
            description="Torneo anual de fútbol interdepartamental",
            max_teams=16,
            start_date=datetime(2023, 9, 10),
            end_date=datetime(2023, 11, 20),
            status_id=1,  # Por ejemplo: 1 = "Planificado"
            created_by=42,
            created_at=datetime(2023, 4, 1)
        ),
        Tournament(
            id=102,
            activity_id=1,
            organization=mock_organization(),
            organization_id=1,
            name="Copa de Fútbol Rápido",
            description="Torneo de fútbol 7",
            max_teams=8,
            start_date=datetime(2023, 12, 5),
            end_date=datetime(2023, 12, 10),
            status_id=2,  # Por ejemplo: 2 = "En progreso"
            created_by=42,
            created_at=datetime(2023, 6, 15)
        )
    ]
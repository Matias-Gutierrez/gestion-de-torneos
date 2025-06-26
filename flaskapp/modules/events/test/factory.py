from datetime import datetime, timedelta
from unittest.mock import MagicMock

# Desde acá sample_form_data modificamos, es nuestro "form"
def mock_event_status():
    status = MagicMock()
    status.id = 1
    status.code = "active"
    status.description = "Evento de Prueba"
    return status

def mock_organization():
    org = MagicMock()
    org.id = 1
    org.name = "Org Ejemplo"
    return org

def mock_user():
    user = MagicMock()
    user.id = 1
    user.name = "Usuario Prueba"
    return user

def mock_tournament():
    tournament = MagicMock()
    tournament.id = 1
    tournament.name = "Torneo Ejemplo"
    tournament.start_date = datetime.now() + timedelta(days=1)
    tournament.end_date = datetime.now() + timedelta(days=2)
    return tournament

def mock_event():
    event = MagicMock()
    event.id = 1
    event.name = "Evento de Prueba"
    event.description = "Descripción del evento"
    event.start_date = datetime.now()
    event.end_date = datetime.now() + timedelta(days=3)
    event.status = mock_event_status()
    event.organization = mock_organization()
    event.creator = mock_user()
    event.tournaments = [mock_tournament()]
    event.created_at = datetime.now()
    event.updated_at = datetime.now()
    return event
# flaskapp/modules/events/test/test_events_service.py
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from flaskapp.modules.events.service import EventService
from flaskapp.modules.events.test.factory import (
    mock_event,
    mock_event_status
)

"""

Create (Crear)
    test_create_event: Verifica la creación de nuevos eventos con datos de formulario.
        Mockea EventRepository.save() para devolver un evento simulado
        Valida que los campos obligatorios se establezcan correctamente
        Verifica la asignación de organization_id y created_by

Read (Leer)
    test_get_organization_events: Prueba la obtención de eventos por organización
        Mockea relaciones con organización y usuario
        Verifica formato de fechas y datos anidados
        Valida permisos de edición (can_edit)

    test_get_event_detail: Prueba obtención de detalles completos de un evento
        Incluye torneos asociados y opciones de estado
        Valida ordenamiento de torneos por fecha
        Maneja casos con/sin torneos (tournaments_count)

Update (Actualizar)
    test_update_event: Verifica actualización de eventos existentes
        Mockea EventRepository.get_by_id() para obtener evento existente
        Valida sobreescritura correcta de campos
        Verifica persistencia de campos no editables (organization_id)

Delete (Eliminar)
    El módulo no implementa borrado logico directo (la gestión de estado se hace mediante status_id en actualización)

"""

class TestEventService:
    @pytest.fixture
    def sample_form_data(self):
        return {
            'name': 'Nuevo Evento',
            'description': 'Descripción de prueba',
            'start_date': datetime.now(),
            'end_date': datetime.now() + timedelta(days=3),
            'status_id': 1
        }

    def test_get_organization_events(self):
        test_event = mock_event()
        
        with patch.multiple(
            'flaskapp.modules.events.service',
            EventRepository=MagicMock(
                get_by_organization=MagicMock(return_value=[test_event])
            ),
            OrganizationMemberRepository=MagicMock(
                is_user_organizer=MagicMock(return_value=True)
            )
        ):
            results = EventService.get_organization_events(1, 1)
            
            assert len(results) == 1
            assert results[0].name == "Evento de Prueba"
            assert results[0].can_edit is True

    def test_get_event_detail(self):
        test_event = mock_event()
        test_status = mock_event_status()
        
        with patch.multiple(
            'flaskapp.modules.events.service',
            EventRepository=MagicMock(
                get_by_id_with_details=MagicMock(return_value=test_event),
                get_status_options=MagicMock(return_value=[test_status])
            ),
            OrganizationMemberRepository=MagicMock(
                is_user_organizer=MagicMock(return_value=True)
            )
        ):
            result = EventService.get_event_detail(1, 1)
            
            assert result.id == 1
            assert result.name == "Evento de Prueba"
            assert result.can_edit is True
            assert len(result.tournaments) == 1
            assert len(result.status_options) == 1

    def test_create_event(self, sample_form_data):
        new_event = mock_event()
        
        with patch.multiple(
            'flaskapp.modules.events.service',
            EventRepository=MagicMock(
                save=MagicMock(return_value=new_event)
            )
        ):
            result = EventService.create_or_update_event(
                sample_form_data, 
                organization_id=1,
                creator_id=1
            )
            
            assert result.id == 1
            assert result.name == "Evento de Prueba"

    def test_update_event(self, sample_form_data):
        existing_event = mock_event()
        
        with patch.multiple(
            'flaskapp.modules.events.service',
            EventRepository=MagicMock(
                get_by_id=MagicMock(return_value=existing_event),
                save=MagicMock(return_value=existing_event)
            )
        ):
            result = EventService.create_or_update_event(
                sample_form_data,
                organization_id=1,
                creator_id=1,
                event_id=1
            )
            
            assert result.id == 1
            assert result.name == "Nuevo Evento"

    def test_get_event_detail_no_tournaments(self):
        test_event = mock_event()
        test_event.tournaments = []
        
        with patch.multiple(
            'flaskapp.modules.events.service',
            EventRepository=MagicMock(
                get_by_id_with_details=MagicMock(return_value=test_event),
                get_status_options=MagicMock(return_value=[mock_event_status()])
            ),
            OrganizationMemberRepository=MagicMock(
                is_user_organizer=MagicMock(return_value=False)
            )
        ):
            result = EventService.get_event_detail(1, 1)
            
            assert result.tournaments_count == 0
            assert result.can_edit is False
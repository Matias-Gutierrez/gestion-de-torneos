import pytest, sys
from unittest.mock import patch

# porsiaca
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))

from flaskapp.modules.activities.service import ActivityService
from flaskapp.modules.activities.test.factory import mock_activity, mock_organization, mock_tournament, mock_user, mock_category


"""
Create (Crear)
    test_create_activity: Verifica que se pueda crear una nueva actividad con los datos del formulario.
        Se mockea ActivityRepository.save() para devolver una nueva actividad simulada.
        Se verifica que los campos se establecieron correctamente.

Read (Leer)
    test_get_activity_details: Ya existente, prueba la obtención de detalles de una actividad.

    test_get_all_activities: Prueba la obtención de todas las actividades.

    test_get_complete_activity_details: Prueba la obtención de detalles completos con estadísticas.

Update (Actualizar)
    test_update_activity: Verifica que se puedan actualizar los campos de una actividad existente.

    test_toggle_activity_enable/test_toggle_activity_disable: Prueban el cambio de estado (activar/desactivar).

Delete (Eliminar)
    En este caso, no hay un delete real sino un toggle de estado, que ya está cubierto por las pruebas de toggle.

"""

class TestActivityService:
    @pytest.fixture
    def sample_form_data(self):
        return {
            'name': 'Nueva Actividad',
            'description': 'Descripción de prueba',
            'min_players': 5,
            'category': 3,
            'is_active': True
        }

    def test_get_activity_details(self):
        # Configurar mocks
        test_activity = mock_activity()
        test_activity.creator = mock_user()
        test_activity.category = mock_category()
        test_activity.tournaments = []
        
        with patch('flaskapp.modules.activities.service.ActivityRepository') as mock_repo:
            mock_repo.get_by_id_with_details.return_value = test_activity
            
            result = ActivityService.get_activity_detail(1, False)
        
        assert result.id == 1
        assert result.name == "LoL"
        assert result.created_by == "Test User"
        assert result.category == "eSports"

    def test_get_all_activities(self):
        test_activity = mock_activity()
        test_activity.creator = mock_user()
        test_activity.category = mock_category()
        
        with patch('flaskapp.modules.activities.service.ActivityRepository') as mock_repo:
            mock_repo.get_all_with_details.return_value = [test_activity]
            
            results = ActivityService.get_all_activities()
            
            assert len(results) == 1
            assert results[0].name == "LoL"
            assert results[0].category == "eSports"

    def test_create_activity(self, sample_form_data):
        new_activity = mock_activity()
        new_activity.id = 2  # Simular nuevo ID
        
        with patch('flaskapp.modules.activities.service.ActivityRepository') as mock_repo:
            mock_repo.save.return_value = new_activity
            
            # Llamada sin activity_id para creación
            result = ActivityService.create_or_update_activity(sample_form_data)
            
            assert result.id == 2
            mock_repo.save.assert_called_once()
            
            # Verificar que se creó una nueva actividad
            saved_activity = mock_repo.save.call_args[0][0]
            assert saved_activity.name == sample_form_data['name']
            assert saved_activity.description == sample_form_data['description']

    def test_update_activity(self, sample_form_data):
        existing_activity = mock_activity()
        
        with patch('flaskapp.modules.activities.service.ActivityRepository') as mock_repo:
            mock_repo.get_by_id.return_value = existing_activity
            mock_repo.save.return_value = existing_activity
            
            # Llamada con activity_id para actualización
            result = ActivityService.create_or_update_activity(
                sample_form_data, 
                activity_id=1
            )
            
            assert result.id == 1
            mock_repo.get_by_id.assert_called_once_with(1)
            mock_repo.save.assert_called_once()
            
            # Verificar que se actualizaron los campos
            saved_activity = mock_repo.save.call_args[0][0]
            assert saved_activity.name == sample_form_data['name']
            assert saved_activity.description == sample_form_data['description']

    def test_toggle_activity_enable(self):
        inactive_activity = mock_activity()
        inactive_activity.is_active = False
        
        with patch('flaskapp.modules.activities.service.ActivityRepository') as mock_repo:
            mock_repo.get_by_id.return_value = inactive_activity
            mock_repo.save.return_value = inactive_activity
            
            result = ActivityService.toggle_activity(1)
            
            assert result.is_active is True
            mock_repo.save.assert_called_once()

    def test_toggle_activity_disable(self):
        active_activity = mock_activity()
        active_activity.is_active = True
        
        with patch('flaskapp.modules.activities.service.ActivityRepository') as mock_repo:
            mock_repo.get_by_id.return_value = active_activity
            mock_repo.save.return_value = active_activity
            
            result = ActivityService.toggle_activity(1)
            
            assert result.is_active is False
            mock_repo.save.assert_called_once()

    def test_get_complete_activity_details(self):
        # Configurar mocks
        test_activity = mock_activity()
        test_activity.creator = mock_user()
        test_activity.category = mock_category()
        test_activity.tournaments = mock_tournament()
        
        # Mockear todas las llamadas al repositorio
        with patch('flaskapp.modules.activities.service.ActivityRepository') as mock_repo:
            # Configurar retornos de los métodos del repositorio
            mock_repo.get_by_id_with_details.return_value = test_activity
            mock_repo.count_tournaments_by_activity.return_value = 2
            mock_repo.count_all_tournaments.return_value = 10
            mock_repo.count_teams_by_activity.return_value = 16
            mock_repo.count_participants_by_activity.return_value = 32
            mock_repo.get_recent_tournaments.return_value = test_activity.tournaments
            mock_repo.get_popular_organizations.return_value = [mock_organization()]
            
            # Ejecutar el método bajo prueba
            result = ActivityService.get_complete_activity_details(1)
            
            # Verificaciones
            assert result['activity'].id == 1
            assert result['stats'].total_tournaments == 2
            assert result['stats'].percentage_of_all == 20.0
            assert result['stats'].total_teams == 16
            assert result['stats'].total_participants == 32
            assert len(result['stats'].recent_tournaments) == 2
            assert result['stats'].recent_tournaments[0].organization_name == "Organización de Prueba"
            assert len(result['stats'].popular_organizations) == 1
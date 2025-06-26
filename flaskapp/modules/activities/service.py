from typing import List
from flaskapp.database.models import Activity 
from flaskapp.modules.activities.dto import ActivityDTO, ActivityDetailDTO
from ..activities.dto import ActivityStats, ActivityTournamentStats

# Se importa el nuevo repositorio
from .repository import ActivityRepository

class ActivityService:

    @staticmethod
    def get_complete_activity_details(activity_id, is_admin=False):    
        activity_dto = ActivityService.get_activity_detail(activity_id, is_admin)
        
        # La lógica de negocio permanece aquí, las llamadas a la BD se van al repositorio
        total_tournaments_all = ActivityRepository.count_all_tournaments()
        
        stats = ActivityStats(
            total_tournaments=ActivityRepository.count_tournaments_by_activity(activity_id),
            percentage_of_all=0,
            total_teams=ActivityRepository.count_teams_by_activity(activity_id),
            total_participants=ActivityRepository.count_participants_by_activity(activity_id),
            recent_tournaments=[],
            popular_organizations=[]
        )
        
        stats.percentage_of_all = round((stats.total_tournaments / total_tournaments_all * 100) if total_tournaments_all > 0 else 0, 1)
        
        recent_tournaments = ActivityRepository.get_recent_tournaments(activity_id, 5)
        stats.recent_tournaments = [
            ActivityTournamentStats(
                id=t.id, name=t.name, organization_name=t.organization.name,
                organization_id=t.organization_id, status=t.status.code if t.status else '',
                start_date=t.start_date.strftime('%Y-%m-%d') if t.start_date else ''
            ) for t in recent_tournaments
        ]
        
        popular_orgs = ActivityRepository.get_popular_organizations(activity_id)
        stats.popular_organizations_count = len(popular_orgs)
        stats.popular_organizations = popular_orgs[:3]
        
        return {
            'activity': activity_dto,
            'stats': stats
        }

    @staticmethod
    def get_all_activities() -> List[ActivityDTO]:
        activities = ActivityRepository.get_all_with_details()
        return [
            ActivityDTO(
                id=a.id, name=a.name, description=a.description,
                min_players=a.min_players_per_team, category=a.category.name if a.category else None,
                is_active=a.is_active, created_by=a.creator.name if a.creator else 'Sistema',
                created_at=a.created_at.strftime('%d-%m-%Y'),
                updated_at=a.updated_at.strftime('%d-%m-%Y') if a.updated_at else ''
            ) for a in activities
        ]

    @staticmethod
    def get_activity_detail(activity_id: int, is_admin: bool) -> ActivityDetailDTO:
        activity = ActivityRepository.get_by_id_with_details(activity_id)
        return ActivityDetailDTO(
            id=activity.id, name=activity.name, description=activity.description,
            min_players=activity.min_players_per_team, category=activity.category.name if activity.category else None,
            is_active=activity.is_active, created_by=activity.creator.name if activity.creator else 'Sistema',
            created_at=activity.created_at.strftime('%Y-%m-%d'),
            updated_at=activity.updated_at.strftime('%Y-%m-%d') if activity.updated_at else '',
            tournaments_count=len(activity.tournaments), can_edit=is_admin
        )

    @staticmethod
    def toggle_activity(activity_id: int):
        activity = ActivityRepository.get_by_id(activity_id)
        activity.is_active = not activity.is_active
        return ActivityRepository.save(activity)

    @staticmethod
    def create_or_update_activity(form_data, activity_id=None):
        if activity_id:
            activity = ActivityRepository.get_by_id(activity_id)
        else:
            activity = Activity()

        activity.name = form_data['name']
        activity.description = form_data['description']
        activity.min_players_per_team = form_data['min_players']
        activity.category_id = form_data['category']
        activity.is_active = form_data['is_active']
        
        return ActivityRepository.save(activity)
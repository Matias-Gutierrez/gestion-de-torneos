from typing import List
from flaskapp.database.models import Activity, Organization, Team, TeamMember, Tournament
from flaskapp.modules.activities.dto import ActivityDTO, ActivityDetailDTO

from flaskapp.database.models import db


from ..activities.dto import ActivityStats, ActivityTournamentStats
from sqlalchemy import func, desc

class ActivityService:

    @staticmethod
    def get_complete_activity_details(activity_id, is_admin=False):    
        # Datos básicos de la actividad
        activity = ActivityService.get_activity_detail(activity_id, is_admin)
        
        # Estadísticas generales
        total_tournaments_all = Tournament.query.count()
        stats = ActivityStats(
            total_tournaments=0,
            percentage_of_all=0,
            total_teams=0,
            total_participants=0,
            recent_tournaments=[],
            popular_organizations=[]
        )
        
        # Torneos de esta actividad
        stats.total_tournaments = Tournament.query.filter_by(activity_id=activity_id).count()
        stats.percentage_of_all = round((stats.total_tournaments / total_tournaments_all * 100) if total_tournaments_all > 0 else 0, 1)
        
        # Equipos en esta actividad
        stats.total_teams = Team.query.join(
            Tournament, Tournament.id == Team.tournament_id
        ).filter(
            Tournament.activity_id == activity_id
        ).count()
        
        # Participantes en esta actividad
        stats.total_participants = TeamMember.query.join(
            Team, Team.id == TeamMember.team_id
        ).join(
            Tournament, Tournament.id == Team.tournament_id
        ).filter(
            Tournament.activity_id == activity_id
        ).distinct(TeamMember.user_id).count()
        
        # Torneos recientes
        recent_tournaments = Tournament.query.join(
            Organization, Organization.id == Tournament.organization_id
        ).filter(
            Tournament.activity_id == activity_id
        ).order_by(
            Tournament.start_date.desc()
        ).limit(5).all()
        
        stats.recent_tournaments = [
            ActivityTournamentStats(
                id=t.id,
                name=t.name,
                organization_name=t.organization.name,
                organization_id=t.organization_id,
                status=t.status.code if t.status else '',
                start_date=t.start_date.strftime('%Y-%m-%d') if t.start_date else ''
            ) for t in recent_tournaments
        ]
        
        # Organizaciones más activas con esta actividad
        stats.popular_organizations = Organization.query.join(
            Tournament, Tournament.organization_id == Organization.id
        ).filter(
            Tournament.activity_id == activity_id
        ).group_by(
            Organization.id
        ).order_by(
            desc(func.count(Tournament.id))
        ).with_entities(
            Organization.id,
            Organization.name,
            func.count(Tournament.id).label('tournament_count')
        ).all()

        stats.popular_organizations_count = len(stats.popular_organizations)
        stats.popular_organizations = stats.popular_organizations[:3]
        
        return {
            'activity': activity,
            'stats': stats
        }

    @staticmethod
    def get_all_activities() -> List[ActivityDTO]:
        activities = Activity.query.options(
            db.joinedload(Activity.creator),
            db.joinedload(Activity.category)
        ).all()
        return [
            ActivityDTO(
                id=a.id,
                name=a.name,
                description=a.description,
                min_players=a.min_players_per_team,
                category=a.category.name if a.category else None,
                is_active=a.is_active,
                created_by=a.creator.name if a.creator else 'Sistema',
                created_at=a.created_at.strftime('%d-%MM-%Y'),
                updated_at=a.updated_at.strftime('%d-%MM-%Y') if a.updated_at else ''
            ) for a in activities
        ]

    @staticmethod
    def get_activity_detail(activity_id: int, is_admin: bool) -> ActivityDetailDTO:
        activity = Activity.query.options(
            db.joinedload(Activity.creator),
            db.joinedload(Activity.category),
            db.joinedload(Activity.tournaments)
        ).get_or_404(activity_id)

        return ActivityDetailDTO(
            id=activity.id,
            name=activity.name,
            description=activity.description,
            min_players=activity.min_players_per_team,
            category=activity.category.name if activity.category else None,
            is_active=activity.is_active,
            created_by=activity.creator.name if activity.creator else 'Sistema',
            created_at=activity.created_at.strftime('%Y-%m-%d'),
            updated_at=activity.updated_at.strftime('%Y-%m-%d') if activity.updated_at else '',
            tournaments_count=len(activity.tournaments),
            can_edit=is_admin
        )

    @staticmethod
    def toggle_activity(activity_id: int):
        activity = Activity.query.get_or_404(activity_id)
        activity.is_active = not activity.is_active
        db.session.commit()
        return activity

    @staticmethod
    def create_or_update_activity(form_data, activity_id=None):
        if activity_id:
            activity = Activity.query.get_or_404(activity_id)
        else:
            activity = Activity()
            #  Check if name is already in use
            existing_activity = Activity.query.filter_by(name=form_data['name']).first()
            if existing_activity:
                raise ValueError('El nombre de la actividad ya está en uso.')
            db.session.add(activity)

        activity.name = form_data['name']
        activity.description = form_data['description']
        activity.min_players_per_team = form_data['min_players']
        activity.category_id = form_data['category']
        activity.is_active = form_data['is_active']
        
        db.session.commit()
        return activity
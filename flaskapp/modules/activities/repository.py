from sqlalchemy import func, desc
from flaskapp.database.models import db, Activity, Tournament, Team, TeamMember, Organization

class ActivityRepository:
    
    @staticmethod
    def get_by_id(activity_id: int) -> Activity:
        return Activity.query.get_or_404(activity_id)

    @staticmethod
    def get_by_id_with_details(activity_id: int) -> Activity:
        return Activity.query.options(
            db.joinedload(Activity.creator),
            db.joinedload(Activity.category),
            db.joinedload(Activity.tournaments)
        ).get_or_404(activity_id)

    @staticmethod
    def get_all_with_details() -> list[Activity]:
        return Activity.query.options(
            db.joinedload(Activity.creator),
            db.joinedload(Activity.category)
        ).all()

    @staticmethod
    def save(activity: Activity) -> Activity:
        db.session.add(activity)
        db.session.commit()
        return activity

    @staticmethod
    def count_all_tournaments() -> int:
        return Tournament.query.count()

    @staticmethod
    def count_tournaments_by_activity(activity_id: int) -> int:
        return Tournament.query.filter_by(activity_id=activity_id).count()

    @staticmethod
    def count_teams_by_activity(activity_id: int) -> int:
        return Team.query.join(
            Tournament, Tournament.id == Team.tournament_id
        ).filter(
            Tournament.activity_id == activity_id
        ).count()

    @staticmethod
    def count_participants_by_activity(activity_id: int) -> int:
        return TeamMember.query.join(
            Team, Team.id == TeamMember.team_id
        ).join(
            Tournament, Tournament.id == Team.tournament_id
        ).filter(
            Tournament.activity_id == activity_id
        ).distinct(TeamMember.user_id).count()

    @staticmethod
    def get_recent_tournaments(activity_id: int, limit: int = 5) -> list[Tournament]:
        return Tournament.query.join(
            Organization, Organization.id == Tournament.organization_id
        ).filter(
            Tournament.activity_id == activity_id
        ).order_by(
            Tournament.start_date.desc()
        ).limit(limit).all()

    @staticmethod
    def get_popular_organizations(activity_id: int) -> list:
        return Organization.query.join(
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
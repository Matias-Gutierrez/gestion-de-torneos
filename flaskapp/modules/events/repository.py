from datetime import datetime
from flaskapp.database.models import db, Event, EventStatus, OrganizationMember, Tournament

class EventRepository:
    
    @staticmethod
    def get_by_id(event_id: int) -> Event:
        return Event.query.get_or_404(event_id)

    @staticmethod
    def get_by_id_with_details(event_id: int) -> Event:
        return Event.query.options(
            db.joinedload(Event.organization),
            db.joinedload(Event.status),
            db.joinedload(Event.creator),
            db.joinedload(Event.tournaments).joinedload(Tournament.activity),
            db.joinedload(Event.tournaments).joinedload(Tournament.status)
        ).get_or_404(event_id)

    @staticmethod
    def get_by_organization(organization_id: int) -> list[Event]:
        return Event.query.filter_by(
            organization_id=organization_id
        ).options(
            db.joinedload(Event.organization),
            db.joinedload(Event.status)
        ).order_by(Event.start_date.desc()).all()
    
    @staticmethod
    def get_status_options() -> list[EventStatus]:
        return EventStatus.query.order_by(EventStatus.id).all()

    @staticmethod
    def save(event: Event) -> Event:
        db.session.add(event)
        db.session.commit()
        return event

class OrganizationMemberRepository:
    
    @staticmethod
    def is_user_organizer(organization_id: int, user_id: int) -> bool:
        return OrganizationMember.query.filter_by(
            organization_id=organization_id,
            user_id=user_id,
            is_organizer=True
        ).first() is not None
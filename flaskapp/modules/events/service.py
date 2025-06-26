from datetime import datetime
from typing import List
from flaskapp.database.models import Event # Solo para type hinting
from flaskapp.modules.events.dto import EventDTO, EventDetailDTO

# Se importan los nuevos repositorios
from .repository import EventRepository, OrganizationMemberRepository

class EventService:
    @staticmethod
    def get_organization_events(organization_id: int, user_id: int) -> List[EventDTO]:
        is_organizer = OrganizationMemberRepository.is_user_organizer(organization_id, user_id)
        events = EventRepository.get_by_organization(organization_id)

        return [
            EventDTO(
                id=e.id, name=e.name, description=e.description,
                start_date=e.start_date.strftime('%Y-%m-%d'),
                end_date=e.end_date.strftime('%Y-%m-%d'),
                status=e.status.code, organization_id=e.organization_id,
                organization_name=e.organization.name, can_edit=is_organizer
            ) for e in events
        ]

    @staticmethod
    def get_event_detail(event_id: int, user_id: int) -> EventDetailDTO:
        event = EventRepository.get_by_id_with_details(event_id)
        is_organizer = OrganizationMemberRepository.is_user_organizer(event.organization_id, user_id)
        status_options = EventRepository.get_status_options()

        sorted_tournaments = sorted(event.tournaments, key=lambda t: t.start_date or datetime.min)

        return EventDetailDTO(
            id=event.id, name=event.name, description=event.description,
            start_date=event.start_date.strftime('%Y-%m-%d'),
            end_date=event.end_date.strftime('%Y-%m-%d'),
            status=event.status.code, organization_id=event.organization_id,
            organization_name=event.organization.name, can_edit=is_organizer,
            creator_name=event.creator.name, created_at=event.created_at.strftime('%Y-%m-%d'),
            updated_at=event.updated_at.strftime('%Y-%m-%d') if event.updated_at else '',
            tournaments_count=len(event.tournaments),
            status_options=[{'code': s.code, 'description': s.description} for s in status_options],
            tournaments=[{
                'id': t.id, 'name': t.name,
                'activity_name': t.activity.name if t.activity else 'N/A',
                'start_date': t.start_date.strftime('%Y-%m-%d') if t.start_date else 'N/A',
                'end_date': t.end_date.strftime('%Y-%m-%d') if t.end_date else 'N/A',
                'status': t.status.code
            } for t in sorted_tournaments]
        )

    @staticmethod
    def create_or_update_event(form_data, organization_id, creator_id, event_id=None):
        if event_id:
            event = EventRepository.get_by_id(event_id)
        else:
            event = Event(
                organization_id=organization_id,
                created_by=creator_id
            )

        event.name = form_data['name']
        event.description = form_data['description']
        event.start_date = form_data['start_date']
        event.end_date = form_data['end_date']
        event.status_id = form_data['status_id']

        return EventRepository.save(event)
from datetime import datetime
from typing import List, Optional
from flask import abort
from flask_login import current_user
from psycopg2 import IntegrityError
from sqlalchemy import and_, or_, not_

from flaskapp.database.models import Match, TeamInvitationStatus, TournamentReferee, db, Team, TeamMember, TeamInvitation, Tournament, OrganizationMember, User
from .dto import TeamMatchDTO, TeamMemberDTO, TeamInvitationDTO, EligibleMemberDTO
from sqlalchemy.orm import aliased


TeamA = aliased(Team, name='team_a')
TeamB = aliased(Team, name='team_b')

class TeamService:
    @staticmethod
    def calculate_team_seed(team_id):
        """
        Calculate the seed score for a team based on ALL its members' performance.
        
        Args:
            team_id (int): ID of the team to calculate seed for
        
        Returns:
            int: The calculated seed score
        """
        
        team = Team.query.get_or_404(team_id)
        total_seed = 0
        
        # Calcular para todos los miembros del equipo
        for member in team.members:
            # Get all matches this member has participated in (as part of any team)
            user_matches = Match.query.join(
                TeamMember, TeamMember.team_id == Match.team_a_id
            ).filter(
                TeamMember.user_id == member.user_id
            ).union(
                Match.query.join(
                    TeamMember, TeamMember.team_id == Match.team_b_id
                ).filter(
                    TeamMember.user_id == member.user_id
                )
            ).all()
            
            # Calculate points from match wins
            for match in user_matches:
                if match.winner_id:
                    # Check if the user was on the winning team
                    user_teams_in_match = [tm.team_id for tm in member.user.team_memberships]
                    if match.winner_id in user_teams_in_match:
                        total_seed += 10  # 10 point for each match win
                        
                        # Check if this was a tournament final
                        if match.level == 0:  # Assuming level 1 is the final
                            total_seed += 15  # Bonus 15 points for tournament win
        
        return total_seed

    @staticmethod
    def get_team_details(team_id: int) -> Team:
        return Team.query.get_or_404(team_id)
    
    @staticmethod
    def is_team_leader(team_id: int, user_id: int) -> bool:
        team_member = TeamMember.query.filter_by(team_id=team_id, user_id=user_id).first()
        if not team_member:
            return False
        return team_member.is_leader
    
    @staticmethod
    def create_team(organization_id, tournament_id, name, leader_id):
        # Obtener datos base
        tournament = Tournament.query.get_or_404(tournament_id)

        # Validación 0: verificar si hay cupo disponible
        current_teams_count = db.session.query(Team).filter_by(tournament_id=tournament_id).count()
        if current_teams_count >= tournament.max_teams:
            raise ValueError(f"No se pueden crear más equipos. El torneo ya alcanzó el máximo de {tournament.max_teams} equipos.")

        # Validación 1: no debe ser admin
        user = User.query.get_or_404(leader_id)
        if user.is_admin:
            raise ValueError("Un administrador no puede crear equipos.")

        # Validación 2: no debe ser organizador de esta organización
        is_organizer = db.session.query(OrganizationMember).filter_by(
            organization_id=organization_id,
            user_id=leader_id,
            is_organizer=True
        ).first()
        if is_organizer:
            raise ValueError("Un organizador no puede crear equipos.")

        # Validación 3: no debe ser árbitro del torneo
        is_referee = db.session.query(TournamentReferee).filter_by(
            tournament_id=tournament_id,
            user_id=leader_id
        ).first()
        if is_referee:
            raise ValueError("Un árbitro no puede crear equipos.")

        # Validación 4: no debe estar en otro equipo del torneo
        is_in_team = db.session.query(TeamMember).join(Team).filter(
            Team.tournament_id == tournament_id,
            TeamMember.user_id == leader_id
        ).first()
        if is_in_team:
            raise ValueError("Ya perteneces a un equipo en este torneo.")

        # Crear el equipo
        new_team = Team(
            tournament_id=tournament_id,
            name=name.strip(),
            created_at=datetime.utcnow()
        )
        db.session.add(new_team)
        try:
            db.session.flush()  # Permite obtener el ID antes de hacer commit
        except IntegrityError:
            db.session.rollback()
            raise ValueError("Ya existe un equipo con ese nombre en este torneo.")

        # Crear entrada en TeamMember como líder
        leader = TeamMember(
            team_id=new_team.id,
            user_id=leader_id,
            is_leader=True
        )
        db.session.add(leader)

        # Calculate initial seed score based on leader's performance
        new_team.seed_score = TeamService.calculate_team_seed(new_team.id)
        
        try:
            db.session.commit()
            return new_team
        except Exception as e:
            db.session.rollback()
            raise "Ha ocurrido un error al crear el equipo :("

    @staticmethod
    def get_team_members(team_id: int) -> List[TeamMemberDTO]:
        members = db.session.query(
            TeamMember,
            User
        ).join(
            User
        ).filter(
            TeamMember.team_id == team_id
        ).all()

        return [
            TeamMemberDTO(
                user_id=member.user_id,
                name=user.name,
                email=user.email,
                profile_picture=user.profile_picture,
                is_leader=member.is_leader,
                joined_at=member.joined_at
            ) for member, user in members
        ]

    @staticmethod
    def get_team_invitations(team_id: int) -> List[TeamInvitationDTO]:
        invitations = db.session.query(
            TeamInvitation,
            User
        ).join(
            User, TeamInvitation.invited_user_id == User.id
        ).filter(
            TeamInvitation.team_id == team_id
        ).all()

        return [
            TeamInvitationDTO(
                id=invitation.id,
                invited_user_id=invitation.invited_user_id,
                invited_user_name=user.name,
                invited_user_email=user.email,
                invited_user_profile_picture=user.profile_picture,
                status=invitation.status.code,
                created_at=invitation.created_at
            ) for invitation, user in invitations
        ]

    @staticmethod
    def get_eligible_members(tournament_id: int, team_id: int, search: str = None) -> List[EligibleMemberDTO]:
        tournament = Tournament.query.get_or_404(tournament_id)

        # Subqueries para exclusión
        existing_members = db.session.query(TeamMember.user_id).filter_by(team_id=team_id).subquery()
        existing_referees = db.session.query(TournamentReferee.user_id).filter_by(tournament_id=tournament_id).subquery()
        other_team_members = db.session.query(TeamMember.user_id).join(Team).filter(
            Team.tournament_id == tournament_id,
            Team.id != team_id
        ).subquery()

        # Invitaciones
        pending_status_id = TeamInvitationStatus.query.filter_by(code='PENDING').first().id
        pending_invitation_ids = db.session.query(TeamInvitation.invited_user_id).filter(
            TeamInvitation.team_id == team_id,
            TeamInvitation.status_id == pending_status_id
        ).subquery()

        non_pending_invited_ids = db.session.query(TeamInvitation.invited_user_id).filter(
            TeamInvitation.team_id == team_id,
            TeamInvitation.status_id != pending_status_id
        ).subquery()

        # Organizadores de la organización
        organization_organizers = db.session.query(OrganizationMember.user_id).filter(
            OrganizationMember.organization_id == tournament.organization_id,
            OrganizationMember.is_organizer == True
        ).subquery()

        # Consulta principal
        query = db.session.query(
            OrganizationMember,
            User
        ).join(
            User,
            OrganizationMember.user_id == User.id
        ).filter(
            OrganizationMember.organization_id == tournament.organization_id,
            OrganizationMember.user_id.notin_(existing_members),
            OrganizationMember.user_id.notin_(existing_referees),
            OrganizationMember.user_id.notin_(other_team_members),
            OrganizationMember.user_id.notin_(non_pending_invited_ids),
            OrganizationMember.user_id.notin_(organization_organizers),  # ✅ Aquí filtramos organizadores
            User.is_admin == False
        )

        if search:
            query = query.filter(
                db.or_(
                    User.name.ilike(f'%{search}%'),
                    User.email.ilike(f'%{search}%')
                )
            )

        results = query.all()

        pending_ids = [inv_id for (inv_id,) in db.session.query(pending_invitation_ids).all()]

        return [
            EligibleMemberDTO(
                user_id=user.id,
                name=user.name,
                email=user.email,
                profile_picture=user.profile_picture,
                is_invited=user.id in pending_ids
            ) for _, user in results
        ]


    @staticmethod
    def toggle_invitation(tournament_id: int, team_id: int, user_id: int):
        tournament = Tournament.query.get_or_404(tournament_id)
        team = Team.query.get_or_404(team_id)
        
        # Verificar si el torneo está en estado de registro abierto
        if tournament.status.code != 'REGISTRATION_OPEN':
            raise ValueError("El torneo no está en fase de registro")
        
        # Verificar si ya existe una invitación pendiente
        pending_status_id = TeamInvitationStatus.query.filter_by(code='PENDING').first().id
        existing_invitation = TeamInvitation.query.filter_by(
            team_id=team_id,
            invited_user_id=user_id,
            status_id=pending_status_id
        ).first()

        if existing_invitation:
            db.session.delete(existing_invitation)
            db.session.commit()
            return 'removed'

        # Verificar si ya pertenece a un equipo del torneo
        is_in_team = db.session.query(TeamMember.id).join(Team).filter(
            Team.tournament_id == tournament_id,
            TeamMember.user_id == user_id
        ).first()

        # Verificar si es árbitro del torneo
        is_referee = db.session.query(TournamentReferee.id).filter_by(
            tournament_id=tournament_id,
            user_id=user_id
        ).first()

        # Verificar si es miembro válido de la organización
        is_member = db.session.query(OrganizationMember).join(User).filter(
            OrganizationMember.organization_id == tournament.organization_id,
            OrganizationMember.user_id == user_id,
            User.is_admin == False
        ).first()

        if not is_member or is_in_team or is_referee:
            raise ValueError("El usuario no cumple los requisitos para ser invitado")

        # Crear la nueva invitación
        new_invitation = TeamInvitation(
            team_id=team_id,
            invited_by_user_id=current_user.id,
            invited_user_id=user_id,
            status_id=pending_status_id
        )
        db.session.add(new_invitation)
        db.session.commit()
        return 'added'


    @staticmethod
    def update_team(team_id: int, name: str):
        team = Team.query.get_or_404(team_id)

        # Validar que el torneo aún esté en estado 'REGISTRATION_OPEN'
        if team.tournament.status.code != 'REGISTRATION_OPEN':
            raise ValueError("El equipo no puede ser modificado porque el torneo ya ha comenzado")

        team.name = name
        db.session.commit()
        return team


    @staticmethod
    def delete_team(team_id: int):
        team = Team.query.get_or_404(team_id)
        db.session.delete(team)
        db.session.commit()


    @staticmethod
    def get_team_matches(team_id: int) -> List[TeamMatchDTO]:
        # Primero creamos subconsultas para los líderes
        team_a_leader_subq = db.session.query(
            TeamMember.team_id,
            User.name,
            User.profile_picture
        ).join(
            User, TeamMember.user_id == User.id
        ).filter(
            TeamMember.is_leader == True
        ).subquery()

        team_b_leader_subq = db.session.query(
            TeamMember.team_id,
            User.name,
            User.profile_picture
        ).join(
            User, TeamMember.user_id == User.id
        ).filter(
            TeamMember.is_leader == True
        ).subquery()

        matches = db.session.query(
            Match,
            TeamA.name.label('team_a_name'),
            TeamB.name.label('team_b_name'),
            User.name.label('best_player_name'),
            User.profile_picture.label('best_player_pic'),
            team_a_leader_subq.c.name.label('team_a_leader'),
            team_a_leader_subq.c.profile_picture.label('team_a_leader_pic'),
            team_b_leader_subq.c.name.label('team_b_leader'),
            team_b_leader_subq.c.profile_picture.label('team_b_leader_pic')
        ).join(
            TeamA, Match.team_a_id == TeamA.id
        ).join(
            TeamB, Match.team_b_id == TeamB.id
        ).outerjoin(
            User, Match.best_player_id == User.id
        ).outerjoin(
            team_a_leader_subq, team_a_leader_subq.c.team_id == Match.team_a_id
        ).outerjoin(
            team_b_leader_subq, team_b_leader_subq.c.team_id == Match.team_b_id
        ).filter(
            or_(
                Match.team_a_id == team_id,
                Match.team_b_id == team_id
            ),
            Match.is_bye == False
        ).order_by(
            Match.level.desc(),
            Match.match_number.asc()
        ).all()

        result = []
        for match in matches:
            result.append(TeamMatchDTO(
                id=match.Match.id,
                level=match.Match.level,
                match_number=match.Match.match_number,
                team_a_id=match.Match.team_a_id,
                team_a_name=match.team_a_name,
                team_a_score=match.Match.score_team_a,
                team_a_leader=match.team_a_leader,
                team_a_leader_pic=match.team_a_leader_pic or '/static/assets/img/theme/team-1.jpg',
                team_b_id=match.Match.team_b_id,
                team_b_name=match.team_b_name,
                team_b_score=match.Match.score_team_b,
                team_b_leader=match.team_b_leader,
                team_b_leader_pic=match.team_b_leader_pic or '/static/assets/img/theme/team-2.jpg',
                winner_id=match.Match.winner_id,
                status=match.Match.status.code,
                completed_at=match.Match.completed_at,
                best_player_name=match.best_player_name,
                best_player_pic=match.best_player_pic or '/static/assets/img/theme/player.jpg'
            ))
        
        return result
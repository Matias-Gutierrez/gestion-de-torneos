import sys
from flask import Blueprint, render_template
from flaskapp.database.models import Notification, NotificationType, RelatedEntityType, Tournament, db
from flaskapp.modules.tournaments.forms import TournamentForm
from flaskapp.modules.tournaments.service import TournamentService

""" Using events_bp blueprint to avoid circular imports """
from flaskapp.modules.notifications.forms import NotifisForm
from flaskapp.modules.notifications.service import NotificationService

notifications_bp = Blueprint(
    'notifications_blueprint',
    __name__, 
    url_prefix='/notifications')

from flask import request, redirect, url_for, flash
from flask_login import current_user, login_required
from flaskapp.modules.auth.decorators import (
    organization_member_required,
    organization_organizer_required
)

@notifications_bp.route('/')
@login_required
def index():
    """
    Display all notifications for the current user
    URL: /notifications/
    """
    notifications = NotificationService.get_notifications(current_user.id)
    return render_template(
        'notifications/index.html', 
        notifications=notifications)


@notifications_bp.route('/mark_as_read/<int:notification_id>', methods=['GET'])
@login_required
def mark_as_read(notification_id):
    """ Mark a notification as read
    URL: /notifications/mark_as_read/<notification_id>
    """
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id != current_user.id:
        flash('No tienes permisos', 'danger')
        return redirect(url_for('notifications_blueprint.index'))
    notification.is_read = True
    db.session.commit()
    # flash('Notificación marcada como leída.', 'success')

    next_url = request.args.get('next')
    if next_url:
        return redirect(next_url)
    return redirect(url_for('notifications_blueprint.index'))  # Fallback
    return redirect(url_for('notifications_blueprint.index'))


@notifications_bp.route('/mark_all_as_read', methods=['GET'])
@login_required
def mark_all_as_read():
    """ Mark all notifications as read
    URL: /notifications/mark_all_as_read
    """
    notifications = NotificationService.get_notifications(current_user.id)
    for notification in notifications:
        if not notification.is_read:
            notification.is_read = True
    db.session.commit()
    flash('Todas las notificaciones han sido marcadas como leídas.', 'success')
    return redirect(url_for('notifications_blueprint.index'))



@notifications_bp.route('/go_to_tournament/<int:tournament_id>', methods=['GET'])
@login_required
def go_to_tournament(tournament_id):
    print(f"Redirecting to tournament {tournament_id} for user {current_user.id}", flush=True)
    tournament = Tournament.query.get_or_404(tournament_id)
    
    # print(f"Tournament details: {type(tournament_id)} Organization_id datatype : {type(tournament.organization_id)}", flush=True)
    return redirect(url_for('tournaments_blueprint.detail', 
                        organization_id=tournament.organization_id, 
                        tournament_id=tournament_id))

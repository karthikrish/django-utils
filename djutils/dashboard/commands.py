import datetime

from django.conf import settings

from djutils.dashboard.models import Panel, PanelData
from djutils.queue.decorators import periodic_command, crontab


# set to 0 or None to prevent data from expiring
EXPIRATION_DAYS = getattr(settings, 'PANEL_DATA_EXPIRATION_DAYS', 7)

@periodic_command(crontab())
def update_panels():
    """
    Simple task which updates the dashboard panels every minute
    """
    Panel.objects.update_panels()

@periodic_command(crontab(hour=0, minute=0))
def remove_old_panel_data():
    """
    Remove old panel data
    """
    if EXPIRATION_DAYS:
        cutoff = datetime.datetime.now() - datetime.timedelta(days=EXPIRATION_DAYS)
        Paneldata.objects.filter(created_date__lte=cutoff).delete()

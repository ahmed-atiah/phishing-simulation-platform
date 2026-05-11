"""
Kampanya otomatik zamanlayıcı.
APScheduler her dakika çalışır:
  - start_date gelmiş, status='Scheduled' → kampanyayı başlat
  - end_date geçmiş,  status='Running'    → kampanyayı tamamla
"""
from apscheduler.schedulers.background import BackgroundScheduler
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

_scheduler = None


def check_campaigns():
    from .models import Campaign
    from .services import start_campaign

    now = timezone.now()

    # Başlatılacak kampanyalar
    to_start = Campaign.objects.filter(status='Scheduled', start_date__lte=now)
    for campaign in to_start:
        logger.info(f"[Scheduler] Kampanya başlatılıyor: {campaign.campaign_name}")
        try:
            start_campaign(campaign.id)
        except Exception as e:
            logger.error(f"[Scheduler] Kampanya başlatma hatası ({campaign.campaign_name}): {e}")

    # Tamamlanacak kampanyalar
    to_finish = Campaign.objects.filter(status='Running', end_date__lte=now)
    for campaign in to_finish:
        logger.info(f"[Scheduler] Kampanya tamamlanıyor: {campaign.campaign_name}")
        campaign.status = 'Completed'
        campaign.save()


def start_scheduler():
    global _scheduler
    if _scheduler is not None:
        return  # Zaten çalışıyor

    _scheduler = BackgroundScheduler(timezone='UTC')
    _scheduler.add_job(
        check_campaigns,
        trigger='interval',
        minutes=1,
        id='campaign_checker',
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("[Scheduler] Kampanya zamanlayıcı başlatıldı (her 1 dakika).")


def stop_scheduler():
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown()
        _scheduler = None

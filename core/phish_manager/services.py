from urllib.parse import unquote
from django.utils import timezone
import uuid
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils.html import strip_tags
from decouple import config
from .models import Campaign, Event, Target

BASE_TRACKING_URL = config('BASE_TRACKING_URL', default='http://127.0.0.1:8000/track/')

def check_campaign_completion(campaign):
    """Marks campaign as Completed if all targets have clicked."""
    total = Event.objects.filter(campaign=campaign).count()
    engaged = Event.objects.filter(campaign=campaign, was_clicked=True).count()

    if total > 0 and engaged == total:
        campaign.status = 'Completed'
        campaign.save()
        print(f"Campaign '{campaign.campaign_name}' marked as Completed.")


def start_campaign(campaign_id):
    try:
        campaign = Campaign.objects.get(id=campaign_id)
    except Campaign.DoesNotExist:
        print(f"Campaign with id {campaign_id} does not exist.")
        return

    email_template = campaign.template

    if campaign.target_group:
        targets = Target.objects.filter(group=campaign.target_group)
        print(f"Starting campaign: {campaign.campaign_name} — group '{campaign.target_group}' ({targets.count()} target(s))...")
    else:
        targets = campaign.targets.all()
        print(f"Starting campaign: {campaign.campaign_name} for {targets.count()} target(s)...")

    for target in targets:
        event = Event.objects.create(campaign=campaign, target=target, status='Sent')
        tracking_link = f"{BASE_TRACKING_URL}{event.unique_event_id}/"

        decoded_body = unquote(email_template.email_body)
        email_body_html = decoded_body.replace("{{TRACKING_LINK}}", tracking_link)
        email_body_html = email_body_html.replace("{{CURRENT_DATE}}", timezone.now().strftime("%d/%m/%Y"))

        pixel_url = f"{BASE_TRACKING_URL}open/{event.unique_event_id}/"
        email_body_html += f'<img src="{pixel_url}" width="1" height="1" style="display:none;" />'

        email_body_plain = strip_tags(email_body_html)
        email_subject = email_template.email_subject

        try:
            msg = EmailMultiAlternatives(
                subject=email_subject,
                body=email_body_plain,
                from_email=settings.DEFAULT_FROM_EMAIL, 
                to=[target.email]
            )
            msg.attach_alternative(email_body_html, "text/html")
            msg.send(fail_silently=False)
            print(f"Successfully sent email to: {target.email}")

        except Exception as e:
            print(f"!!! Failed to send email to {target.email}: {e}")
            event.status = 'Failed'
            event.save()

    campaign.status = 'Running'
    campaign.save()
    print(f"Campaign finished: {campaign.campaign_name}")
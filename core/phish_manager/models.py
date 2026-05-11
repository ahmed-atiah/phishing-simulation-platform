import uuid
from django.db import models
from ckeditor.fields import RichTextField  # <-- Import the Rich Text Editor field

# 1. EmailTemplate Table
class EmailTemplate(models.Model):
    LANDING_PAGE_CHOICES = [
        ('linkedin',   'LinkedIn'),
        ('instagram',  'Instagram'),
        ('microsoft',  'Microsoft 365'),
        ('google',     'Google Workspace'),
    ]

    template_name = models.CharField(max_length=200)
    email_subject = models.CharField(max_length=255)
    email_body = RichTextField()
    created_at = models.DateTimeField(auto_now_add=True)
    landing_page = models.CharField(
        max_length=50,
        choices=LANDING_PAGE_CHOICES,
        default='linkedin'
    )

    def __str__(self):
        return self.template_name

# 2. Target Table
class Target(models.Model):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    group = models.CharField(max_length=100, blank=True) # blank=True means this field is optional

    def __str__(self):
        return self.email

# 3. Campaign Table
class Campaign(models.Model):
    STATUS_CHOICES = [
        ('Scheduled', 'Scheduled'),
        ('Running', 'Running'),
        ('Completed', 'Completed'),
    ]

    campaign_name = models.CharField(max_length=200)
    # Define the relationship: Each campaign is linked to one template
    template = models.ForeignKey(EmailTemplate, on_delete=models.PROTECT)
    # A campaign can target many users
    targets = models.ManyToManyField(Target, blank=True)
    # If set, ALL targets in this group are included (overrides targets field)
    target_group = models.CharField(
        max_length=100,
        blank=True,
        help_text="Grup adı girilirse (örn: 'öğrenci', 'akademisyen') o gruptaki tüm hedeflere gönderilir. Boş bırakılırsa yukarıdaki 'targets' listesi kullanılır."
    )
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Scheduled')

    def __str__(self):
        return self.campaign_name

# 4. Event (Result) Table
class Event(models.Model):
    STATUS_CHOICES = [
        ('Sent', 'Sent'),
        ('Opened', 'Opened'),
        ('Clicked', 'Clicked'),
        ('Submitted', 'Submitted'),
    ]

    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    target = models.ForeignKey(Target, on_delete=models.CASCADE)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Sent')
    last_updated = models.DateTimeField(auto_now=True)
    unique_event_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # Independent tracking flags
    was_opened = models.BooleanField(default=False)
    was_clicked = models.BooleanField(default=False)
    was_submitted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.target.email} in {self.campaign.campaign_name} - {self.status}"
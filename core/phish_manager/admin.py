from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponse
from unfold.admin import ModelAdmin
from .models import EmailTemplate, Target, Campaign, Event
from .services import start_campaign
from .reports import generate_pdf_report, generate_word_report


def launch_campaign(modeladmin, request, queryset):
    for campaign in queryset:
        if campaign.status == 'Scheduled':
            start_campaign(campaign.id)
            messages.success(request, f"✓ Campaign '{campaign.campaign_name}' launched successfully!")
        elif campaign.status == 'Running':
            messages.warning(request, f"⚠ Campaign '{campaign.campaign_name}' is already running.")
        elif campaign.status == 'Completed':
            messages.error(request, f"✗ Campaign '{campaign.campaign_name}' is already completed.")

launch_campaign.short_description = "🚀 Launch selected campaigns"


def mark_completed(modeladmin, request, queryset):
    for campaign in queryset:
        if campaign.status == 'Running':
            campaign.status = 'Completed'
            campaign.save()
            messages.success(request, f"✓ Campaign '{campaign.campaign_name}' marked as Completed.")
        else:
            messages.warning(request, f"⚠ Campaign '{campaign.campaign_name}' is not Running.")

mark_completed.short_description = "✓ Mark selected campaigns as Completed"


def download_pdf_report(modeladmin, request, queryset):
    if queryset.count() != 1:
        messages.error(request, "Lütfen PDF rapor için tek bir kampanya seçin.")
        return
    campaign = queryset.first()
    buffer = generate_pdf_report(campaign)
    safe_name = campaign.campaign_name.replace(' ', '_')
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{safe_name}_rapor.pdf"'
    return response

download_pdf_report.short_description = "📄 PDF rapor indir"


def download_word_report(modeladmin, request, queryset):
    if queryset.count() != 1:
        messages.error(request, "Lütfen Word rapor için tek bir kampanya seçin.")
        return
    campaign = queryset.first()
    buffer = generate_word_report(campaign)
    safe_name = campaign.campaign_name.replace(' ', '_')
    response = HttpResponse(
        buffer,
        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )
    response['Content-Disposition'] = f'attachment; filename="{safe_name}_rapor.docx"'
    return response

download_word_report.short_description = "📝 Word rapor indir"


@admin.register(EmailTemplate)
class EmailTemplateAdmin(ModelAdmin):
    list_display = ('template_name', 'email_subject', 'created_at')
    search_fields = ('template_name', 'email_subject')


@admin.register(Target)
class TargetAdmin(ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'group')
    search_fields = ('email', 'first_name', 'last_name')
    list_filter = ('group',)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['csv_import_url'] = '/targets/import/'
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(Campaign)
class CampaignAdmin(ModelAdmin):
    list_display = ('campaign_name', 'template', 'target_group', 'status', 'start_date', 'end_date')
    list_filter = ('status', 'target_group')
    search_fields = ('campaign_name',)
    actions = [launch_campaign, mark_completed, download_pdf_report, download_word_report]
    fieldsets = (
        (None, {
            'fields': ('campaign_name', 'template', 'status', 'start_date', 'end_date')
        }),
        ('Hedef Kitle', {
            'description': (
                'Grup adı girilirse o gruptaki TÜM hedeflere gönderilir. '
                'Boş bırakılırsa aşağıdaki "Targets" listesi kullanılır.'
            ),
            'fields': ('target_group', 'targets'),
        }),
    )


@admin.register(Event)
class EventAdmin(ModelAdmin):
    list_display = ('target', 'campaign', 'status', 'was_opened', 'was_clicked', 'was_submitted', 'last_updated')
    list_filter = ('status', 'was_clicked', 'was_submitted')
    search_fields = ('target__email', 'campaign__campaign_name')
    readonly_fields = ('unique_event_id', 'last_updated')
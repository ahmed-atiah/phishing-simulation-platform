import csv
import io
import uuid
import threading

from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST


def _launch_in_background(campaign_id):
    from .services import start_campaign
    try:
        start_campaign(campaign_id)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"[BG] Kampanya {campaign_id} başlatma hatası: {e}")

from .models import Campaign, Event, Target
from .services import check_campaign_completion
from .reports import generate_pdf_report, generate_word_report


# ─── Auth ─────────────────────────────────────────────────────────────────────

def panel_login(request):
    if request.user.is_authenticated:
        return redirect('/dashboard/')
    if request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST.get('username'),
            password=request.POST.get('password'),
        )
        if user:
            login(request, user)
            return redirect(request.GET.get('next', '/dashboard/'))
        return render(request, 'login.html', {'form': type('F', (), {'errors': True})()})
    return render(request, 'login.html', {'form': type('F', (), {'errors': False})()})


def panel_logout(request):
    logout(request)
    return redirect('/login/')


def set_language(request):
    if request.method == 'POST':
        lang = request.POST.get('lang', 'tr')
        if lang in ('tr', 'en'):
            request.session['lang'] = lang
    return redirect(request.META.get('HTTP_REFERER', '/dashboard/'))

PHISHING_LANDING_PAGE_URL = "/phish/login/?id="


def track_open(request, event_id):
    try:
        validated_uuid = uuid.UUID(str(event_id))
        event = get_object_or_404(Event, unique_event_id=validated_uuid)
        if not event.was_opened:
            event.was_opened = True
            event.status = 'Opened'
            event.save()
    except (ValueError, TypeError):
        pass

    pixel = (
        b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00'
        b'\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x00\x00\x00\x00'
        b'\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02'
        b'\x44\x01\x00\x3b'
    )
    return HttpResponse(pixel, content_type='image/gif')


def track_click(request, event_id):
    try:
        validated_uuid = uuid.UUID(str(event_id))
    except ValueError:
        raise Http404("Invalid tracking link.")

    event = get_object_or_404(Event, unique_event_id=validated_uuid)

    if not event.was_clicked:
        event.was_clicked = True
        event.status = 'Clicked'
        # Pixel tracking is blocked by most email clients (Gmail, Hotmail, etc.)
        # Clicking the link implies the email was opened, so mark it here too.
        if not event.was_opened:
            event.was_opened = True
        event.save()
        check_campaign_completion(event.campaign)

    return redirect(f"{PHISHING_LANDING_PAGE_URL}{event.unique_event_id}")


def phishing_login(request):
    event_id = request.GET.get('id')
    if not event_id:
        raise Http404()

    try:
        validated_uuid = uuid.UUID(str(event_id))
        event = get_object_or_404(Event, unique_event_id=validated_uuid)
    except (ValueError, TypeError):
        raise Http404()

    # Pick the fake page based on the campaign's email template
    landing_page = event.campaign.template.landing_page
    template_map = {
        'linkedin':  'linkedin_login.html',
        'instagram': 'instagram_login.html',
        'microsoft': 'microsoft_login.html',
        'google':    'google_login.html',
    }
    template_name = template_map.get(landing_page, 'linkedin_login.html')

    return render(request, template_name, {'event_id': event_id})


def submit_credentials(request):
    if request.method == 'POST':
        event_id = request.POST.get('event_id')
        try:
            validated_uuid = uuid.UUID(str(event_id))
            event = get_object_or_404(Event, unique_event_id=validated_uuid)
            if not event.was_submitted:
                event.was_submitted = True
                event.was_clicked = True
                event.was_opened = True
                event.status = 'Submitted'
                event.save()
                check_campaign_completion(event.campaign)
        except (ValueError, TypeError):
            pass
        return redirect(f"/phish/awareness/?id={event_id}")
    raise Http404()


def awareness(request):
    return render(request, 'awareness.html')


@login_required(login_url='/login/')
def download_report(request, campaign_id, fmt):
    campaign = get_object_or_404(Campaign, id=campaign_id)
    safe_name = campaign.campaign_name.replace(' ', '_')

    if fmt == 'pdf':
        buffer = generate_pdf_report(campaign)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{safe_name}_rapor.pdf"'
        return response

    if fmt == 'docx':
        buffer = generate_word_report(campaign)
        response = HttpResponse(
            buffer,
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        response['Content-Disposition'] = f'attachment; filename="{safe_name}_rapor.docx"'
        return response

    raise Http404("Geçersiz format. 'pdf' veya 'docx' kullanın.")


# ─── Panel views (login required) ────────────────────────────────────────────

@login_required(login_url='/login/')
def panel_campaigns(request):
    campaigns = Campaign.objects.select_related('template').order_by('-id')
    return render(request, 'panel/campaigns.html', {'campaigns': campaigns})


@login_required(login_url='/login/')
def panel_campaign_new(request):
    from .models import EmailTemplate
    from django.utils import timezone

    templates = EmailTemplate.objects.all()
    targets   = Target.objects.all().order_by('group', 'last_name')
    groups    = Target.objects.values_list('group', flat=True).distinct().exclude(group='')

    if request.method == 'POST':
        name         = request.POST.get('campaign_name', '').strip()
        template_id  = request.POST.get('template_id')
        target_group = request.POST.get('target_group', '').strip()
        target_ids   = request.POST.getlist('target_ids')
        start_date   = request.POST.get('start_date')
        end_date     = request.POST.get('end_date')
        action       = request.POST.get('action', 'save')

        try:
            from .models import EmailTemplate
            from django.utils.dateparse import parse_datetime
            from django.utils import timezone as tz
            tmpl = EmailTemplate.objects.get(id=template_id)

            def make_aware_dt(s):
                dt = parse_datetime(s)
                if dt and tz.is_naive(dt):
                    dt = tz.make_aware(dt)
                return dt

            campaign = Campaign.objects.create(
                campaign_name=name,
                template=tmpl,
                target_group=target_group,
                start_date=make_aware_dt(start_date),
                end_date=make_aware_dt(end_date),
                status='Scheduled',
            )
            if not target_group and target_ids:
                campaign.targets.set(Target.objects.filter(id__in=target_ids))

            if action == 'launch':
                t = threading.Thread(target=_launch_in_background, args=(campaign.id,), daemon=True)
                t.start()

            from django.contrib import messages as dj_messages
            dj_messages.success(request, f"Kampanya '{name}' oluşturuldu.")
            return redirect('/panel/campaigns/')
        except Exception as e:
            return render(request, 'panel/campaign_new.html', {
                'templates': templates, 'targets': targets, 'groups': groups,
                'error': str(e),
            })

    return render(request, 'panel/campaign_new.html', {
        'templates': templates,
        'targets':   targets,
        'groups':    groups,
    })


@login_required(login_url='/login/')
def panel_campaign_launch(request, campaign_id):
    if request.method == 'POST':
        campaign = get_object_or_404(Campaign, id=campaign_id)
        if campaign.status == 'Scheduled':
            t = threading.Thread(target=_launch_in_background, args=(campaign.id,), daemon=True)
            t.start()
            from django.contrib import messages as dj_messages
            dj_messages.success(request, f"'{campaign.campaign_name}' başlatıldı.")
        return redirect('/panel/campaigns/')
    raise Http404()


@login_required(login_url='/login/')
def panel_campaign_complete(request, campaign_id):
    if request.method == 'POST':
        campaign = get_object_or_404(Campaign, id=campaign_id)
        if campaign.status == 'Running':
            campaign.status = 'Completed'
            campaign.save()
            from django.contrib import messages as dj_messages
            dj_messages.success(request, f"'{campaign.campaign_name}' tamamlandı.")
        return redirect('/panel/campaigns/')
    raise Http404()


@login_required(login_url='/login/')
def panel_email_preview(request):
    from .models import EmailTemplate
    templates  = EmailTemplate.objects.all()
    success_id = request.GET.get('success_id')
    error_id   = request.GET.get('error_id')
    return render(request, 'panel/email_preview.html', {
        'templates':  templates,
        'success_id': success_id,
        'error_id':   error_id,
        'test_email': request.GET.get('test_email', ''),
        'error_msg':  request.GET.get('error_msg', ''),
    })


@login_required(login_url='/login/')
def panel_test_send(request):
    if request.method != 'POST':
        raise Http404()

    from .models import EmailTemplate
    from urllib.parse import unquote
    from django.core.mail import EmailMultiAlternatives
    from django.conf import settings as dj_settings
    from django.utils.html import strip_tags

    template_id = request.POST.get('template_id')
    test_email  = request.POST.get('test_email', '').strip()

    try:
        tmpl = EmailTemplate.objects.get(id=template_id)
        body = unquote(tmpl.email_body)
        body = body.replace('{{TRACKING_LINK}}', '#TEST_LINK')
        body = body.replace('{{CURRENT_DATE}}', '—')

        msg = EmailMultiAlternatives(
            subject=f"[TEST] {tmpl.email_subject}",
            body=strip_tags(body),
            from_email=dj_settings.DEFAULT_FROM_EMAIL,
            to=[test_email],
        )
        msg.attach_alternative(body, 'text/html')
        msg.send(fail_silently=False)
        return redirect(f'/panel/templates/?success_id={template_id}&test_email={test_email}')
    except Exception as e:
        return redirect(f'/panel/templates/?error_id={template_id}&error_msg={e}')


@login_required(login_url='/login/')
def panel_risk(request):
    """
    Risk skoru hesaplama:
      Submitted → 3 puan  (en yüksek risk)
      Clicked   → 2 puan
      Opened    → 1 puan
      Sent only → 0 puan
    Risk seviyesi:
      0        → Güvenli
      1-2      → Düşük
      3-4      → Orta
      5+       → Yüksek
    """
    import json
    from django.db.models import Count

    events = Event.objects.select_related('target', 'campaign').all()

    # Her target için toplam skor
    target_scores = {}
    for ev in events:
        t = ev.target
        if t.id not in target_scores:
            target_scores[t.id] = {
                'target': t, 'score': 0,
                'submitted': 0, 'clicked': 0, 'opened': 0, 'sent': 0
            }
        target_scores[t.id]['sent'] += 1
        if ev.was_submitted:
            target_scores[t.id]['score']     += 3
            target_scores[t.id]['submitted'] += 1
        elif ev.was_clicked:
            target_scores[t.id]['score']     += 2
            target_scores[t.id]['clicked']   += 1
        elif ev.was_opened:
            target_scores[t.id]['score']     += 1
            target_scores[t.id]['opened']    += 1

    def risk_level(score):
        if score == 0: return ('Güvenli', 'safe')
        if score <= 2: return ('Düşük',   'low')
        if score <= 4: return ('Orta',    'medium')
        return ('Yüksek', 'high')

    targets_risk = []
    for data in sorted(target_scores.values(), key=lambda x: -x['score']):
        label, cls = risk_level(data['score'])
        targets_risk.append({**data, 'risk_label': label, 'risk_class': cls})

    # Grup bazlı analiz
    group_stats = {}
    for data in target_scores.values():
        g = data['target'].group or 'Grupsuz'
        if g not in group_stats:
            group_stats[g] = {'sent': 0, 'clicked': 0, 'submitted': 0, 'score_total': 0, 'count': 0}
        group_stats[g]['sent']        += data['sent']
        group_stats[g]['clicked']     += data['clicked']
        group_stats[g]['submitted']   += data['submitted']
        group_stats[g]['score_total'] += data['score']
        group_stats[g]['count']       += 1

    groups_risk = []
    for g, s in sorted(group_stats.items(), key=lambda x: -(x[1]['score_total'])):
        avg = round(s['score_total'] / s['count'], 1) if s['count'] else 0
        click_rate = round(s['clicked'] / s['sent'] * 100, 1) if s['sent'] else 0
        sub_rate   = round(s['submitted'] / s['sent'] * 100, 1) if s['sent'] else 0
        label, cls = risk_level(avg)
        groups_risk.append({
            'group': g, 'count': s['count'],
            'click_rate': click_rate, 'sub_rate': sub_rate,
            'avg_score': avg, 'risk_label': label, 'risk_class': cls,
        })

    # Chart data
    chart_groups     = json.dumps([g['group']      for g in groups_risk])
    chart_click_rate = json.dumps([g['click_rate'] for g in groups_risk])
    chart_sub_rate   = json.dumps([g['sub_rate']   for g in groups_risk])

    # Genel özet
    total = len(target_scores)
    high_risk = sum(1 for d in target_scores.values() if risk_level(d['score'])[1] == 'high')
    med_risk  = sum(1 for d in target_scores.values() if risk_level(d['score'])[1] == 'medium')

    return render(request, 'panel/risk.html', {
        'targets_risk':     targets_risk,
        'groups_risk':      groups_risk,
        'chart_groups':     chart_groups,
        'chart_click_rate': chart_click_rate,
        'chart_sub_rate':   chart_sub_rate,
        'total':            total,
        'high_risk':        high_risk,
        'med_risk':         med_risk,
    })


@login_required(login_url='/login/')
def panel_group_detail(request, group_name):
    targets = Target.objects.filter(group=group_name).order_by('last_name', 'first_name')
    events  = Event.objects.filter(target__group=group_name).select_related('target', 'campaign')

    camps = {}
    for ev in events:
        cid = ev.campaign.id
        if cid not in camps:
            camps[cid] = {'campaign': ev.campaign, 'ev_map': {}}
        tid = ev.target.id
        if tid not in camps[cid]['ev_map']:
            camps[cid]['ev_map'][tid] = {
                'target': ev.target, 'sent': True,
                'opened': False, 'clicked': False, 'submitted': False,
            }
        d = camps[cid]['ev_map'][tid]
        if ev.was_submitted: d['submitted'] = d['clicked'] = d['opened'] = True
        elif ev.was_clicked:  d['clicked']  = d['opened'] = True
        elif ev.was_opened:   d['opened']   = True

    campaigns_data = []
    for cid, data in sorted(camps.items(), key=lambda x: -x[0]):
        rows = []
        sc = oc = cc = sub = 0
        for t in targets:
            row = data['ev_map'].get(t.id, {
                'target': t, 'sent': False, 'opened': False,
                'clicked': False, 'submitted': False,
            })
            rows.append(row)
            if row['sent']:      sc  += 1
            if row['opened']:    oc  += 1
            if row['clicked']:   cc  += 1
            if row['submitted']: sub += 1
        campaigns_data.append({
            'campaign': data['campaign'], 'rows': rows,
            'sent_count': sc, 'opened_count': oc,
            'clicked_count': cc, 'submitted_count': sub,
        })

    return render(request, 'panel/group_detail.html', {
        'group_name':     group_name,
        'target_count':   targets.count(),
        'campaigns_data': campaigns_data,
    })


@login_required(login_url='/login/')
def panel_target_add(request):
    if request.method == 'POST':
        email      = request.POST.get('email', '').strip().lower()
        first_name = request.POST.get('first_name', '').strip()
        last_name  = request.POST.get('last_name', '').strip()
        group      = request.POST.get('group', '').strip()
        if email:
            _, created = Target.objects.update_or_create(
                email=email,
                defaults={'first_name': first_name, 'last_name': last_name, 'group': group},
            )
            from django.contrib import messages as dj_messages
            if created:
                dj_messages.success(request, f"{first_name} {last_name} eklendi.")
            else:
                dj_messages.success(request, f"{first_name} {last_name} güncellendi.")
        return redirect('/panel/targets/')
    return redirect('/panel/targets/')


@login_required(login_url='/login/')
def panel_target_delete(request, target_id):
    if request.method == 'POST':
        target = get_object_or_404(Target, id=target_id)
        name = f"{target.first_name} {target.last_name}"
        target.delete()
        from django.contrib import messages as dj_messages
        dj_messages.success(request, f"{name} silindi.")
    return redirect('/panel/targets/')


@login_required(login_url='/login/')
def panel_targets(request):
    from django.db.models import Count
    active_group = request.GET.get('group', '')
    qs = Target.objects.all()
    if active_group:
        qs = qs.filter(group=active_group)

    from django.db.models import Count as _Count
    # Tek sorguda grup adı + üye sayısı
    group_counts = [
        (row['group'], row['cnt'])
        for row in (
            Target.objects
            .exclude(group='')
            .values('group')
            .annotate(cnt=_Count('id'))
            .order_by('group')
        )
    ]

    return render(request, 'panel/targets.html', {
        'targets':      qs.order_by('group', 'last_name'),
        'groups':       group_counts,
        'active_group': active_group,
        'total':        Target.objects.count(),
    })


@login_required(login_url='/login/')
def import_targets_csv(request):
    """
    GET  → CSV import formu
    POST → CSV dosyasını işle, Target kayıtlarını oluştur/güncelle
    Beklenen CSV formatı (başlık satırı zorunlu):
        email,first_name,last_name,group
    """
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        if not csv_file:
            return render(request, 'import_targets.html', {'error': 'Dosya seçilmedi.'})
        if not csv_file.name.endswith('.csv'):
            return render(request, 'import_targets.html', {'error': 'Sadece .csv dosyası yükleyin.'})

        decoded = csv_file.read().decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(decoded))

        required = {'email', 'first_name', 'last_name'}
        if not required.issubset({h.strip().lower() for h in (reader.fieldnames or [])}):
            return render(request, 'import_targets.html', {
                'error': 'CSV başlıkları hatalı. Gerekli: email, first_name, last_name (group opsiyonel)'
            })

        created = updated = skipped = 0
        errors = []
        for i, row in enumerate(reader, start=2):
            email = row.get('email', '').strip().lower()
            if not email:
                errors.append(f"Satır {i}: e-posta boş, atlandı.")
                skipped += 1
                continue

            defaults = {
                'first_name': row.get('first_name', '').strip(),
                'last_name':  row.get('last_name',  '').strip(),
                'group':      row.get('group', '').strip(),
            }
            _, was_created = Target.objects.update_or_create(email=email, defaults=defaults)
            if was_created:
                created += 1
            else:
                updated += 1

        return render(request, 'import_targets.html', {
            'success': True,
            'created': created,
            'updated': updated,
            'skipped': skipped,
            'errors':  errors,
        })

    return render(request, 'import_targets.html')


@login_required(login_url='/login/')
def dashboard(request):
    import json
    campaigns = Campaign.objects.all()

    campaign_data = []
    total_sent = total_opened = total_clicked = total_submitted = 0

    chart_labels   = []
    chart_sent     = []
    chart_opened   = []
    chart_clicked  = []
    chart_submitted= []

    for campaign in campaigns:
        events = Event.objects.filter(campaign=campaign)
        sent      = events.count()
        opened    = events.filter(was_opened=True).count()
        clicked   = events.filter(was_clicked=True).count()
        submitted = events.filter(was_submitted=True).count()

        click_rate_num = round(clicked / sent * 100, 1) if sent > 0 else 0
        click_rate     = f"{click_rate_num}%"

        total_sent      += sent
        total_opened    += opened
        total_clicked   += clicked
        total_submitted += submitted

        campaign_data.append({
            'campaign':        campaign,
            'sent':            sent,
            'opened':          opened,
            'clicked':         clicked,
            'submitted':       submitted,
            'click_rate':      click_rate,
            'click_rate_num':  click_rate_num,
        })

        chart_labels.append(campaign.campaign_name)
        chart_sent.append(sent)
        chart_opened.append(opened)
        chart_clicked.append(clicked)
        chart_submitted.append(submitted)

    context = {
        'campaign_data':   campaign_data,
        'total_sent':      total_sent,
        'total_opened':    total_opened,
        'total_clicked':   total_clicked,
        'total_submitted': total_submitted,
        # Chart.js JSON verileri
        'chart_labels':    json.dumps(chart_labels),
        'chart_sent':      json.dumps(chart_sent),
        'chart_opened':    json.dumps(chart_opened),
        'chart_clicked':   json.dumps(chart_clicked),
        'chart_submitted': json.dumps(chart_submitted),
        'donut_data':      json.dumps([total_opened, total_clicked, total_submitted,
                                       max(total_sent - total_opened, 0)]),
    }
    return render(request, 'dashboard.html', context)
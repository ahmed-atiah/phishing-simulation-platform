from django.urls import path
from django.shortcuts import redirect
from . import views

urlpatterns = [
    # ── Root → login'e yönlendir
    path('', lambda request: redirect('/login/' if not request.user.is_authenticated else '/dashboard/')),

    # ── Auth
    path('login/',    views.panel_login,    name='login'),
    path('logout/',   views.panel_logout,   name='logout'),
    path('lang/set/', views.set_language,   name='set_language'),

    # ── Phishing tracking (auth gerektirmez — hedef kullanıcılar erişir)
    path('track/<uuid:event_id>/',      views.track_click,        name='track_click'),
    path('track/open/<uuid:event_id>/', views.track_open,         name='track_open'),
    path('phish/login/',                views.phishing_login,     name='phishing_login'),
    path('phish/submit/',               views.submit_credentials, name='submit_credentials'),
    path('phish/awareness/',            views.awareness,          name='awareness'),

    # ── Panel (login required)
    path('dashboard/',                  views.dashboard,          name='dashboard'),
    path('report/<int:campaign_id>/<str:fmt>/', views.download_report,    name='download_report'),
    path('targets/import/',             views.import_targets_csv,          name='import_targets_csv'),
    path('panel/campaigns/',            views.panel_campaigns,             name='panel_campaigns'),
    path('panel/campaigns/new/',        views.panel_campaign_new,          name='panel_campaign_new'),
    path('panel/campaigns/<int:campaign_id>/launch/',   views.panel_campaign_launch,   name='panel_campaign_launch'),
    path('panel/campaigns/<int:campaign_id>/complete/', views.panel_campaign_complete, name='panel_campaign_complete'),
    path('panel/targets/',              views.panel_targets,               name='panel_targets'),
    path('panel/targets/add/',                      views.panel_target_add,    name='panel_target_add'),
    path('panel/targets/<int:target_id>/delete/',   views.panel_target_delete, name='panel_target_delete'),
    path('panel/targets/group/<str:group_name>/',   views.panel_group_detail,  name='panel_group_detail'),
    path('panel/templates/',            views.panel_email_preview,         name='panel_email_preview'),
    path('panel/templates/test-send/',  views.panel_test_send,             name='panel_test_send'),
    path('panel/risk/',                 views.panel_risk,                  name='panel_risk'),
]

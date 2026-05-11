from .lang import TRANSLATIONS

def language(request):
    lang = request.session.get('lang', 'tr')
    if lang not in TRANSLATIONS:
        lang = 'tr'
    return {
        't': TRANSLATIONS[lang],
        'LANG': lang,
    }

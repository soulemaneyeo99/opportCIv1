from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts'  # ✅ CORRIGÉ
    verbose_name = _('Comptes Utilisateurs')
    
    def ready(self):
        # Import des signals si nécessaire
        try:
            import apps.accounts.signals
        except ImportError:
            pass

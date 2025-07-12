from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Quartier

@receiver(pre_save, sender=Quartier)
def set_default_code_postal(sender, instance, **kwargs):
    if not instance.code_postal and instance.ville:
        instance.code_postal = instance.ville.code_postal

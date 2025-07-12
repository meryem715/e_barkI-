from django.contrib import admin
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.contrib import messages

from core.models import (
    Ville, Quartier, TypeE_Barkia, ClientMoral, Personnel,
    E_Barkia, Livraison, Prix, Paiement, Inscription
)

# ---------------------------------------------------------------------------
# Modèles de référence
# ---------------------------------------------------------------------------
@admin.register(Ville)
class VilleAdmin(admin.ModelAdmin):
    list_display = ["nom", "code_postal"]
    search_fields = ["nom", "code_postal"]


@admin.register(Quartier)
class QuartierAdmin(admin.ModelAdmin):
    list_display = ["nom", "ville", "code_postal"]
    list_filter = ["ville"]
    search_fields = ["nom", "code_postal"]


@admin.register(TypeE_Barkia)
class TypeE_BarkiaAdmin(admin.ModelAdmin):
    list_display = ["nom"]
    search_fields = ["nom"]


@admin.register(ClientMoral)
class ClientMoralAdmin(admin.ModelAdmin):
    list_display = [
        "ice",
        "intitulé",
        "type",
        "gsm",
        "email",
        "ville",
        "quartier",
    ]
    list_filter = ["type", "ville"]
    search_fields = ["ice", "intitulé", "email"]


@admin.register(Personnel)
class PersonnelAdmin(admin.ModelAdmin):
    list_display = ["cin", "nom", "prénom", "poste", "email"]
    list_filter = ["poste"]
    search_fields = ["nom", "prénom", "cin"]


@admin.register(E_Barkia)
class EBarkiaAdmin(admin.ModelAdmin):
    list_display = [
        "code_e_barkia",
        "objet",
        "type",
        "statut",
        "client",
        "date_envoi",
    ]
    list_filter = ["statut", "type", "date_envoi"]
    search_fields = ["code_e_barkia", "objet"]
    autocomplete_fields = ["client", "type_format"]


@admin.register(Livraison)
class LivraisonAdmin(admin.ModelAdmin):
    list_display = ["e_barkia", "employé", "date_livraison", "heure_livraison"]
    list_filter = ["date_livraison"]
    search_fields = ["e_barkia__code_e_barkia"]


@admin.register(Prix)
class PrixAdmin(admin.ModelAdmin):
    list_display = ["prix_par_lettre", "date_effet"]
    list_filter = ["date_effet"]


@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ["e_barkia", "montant", "date_paiement"]
    list_filter = ["date_paiement"]
    search_fields = ["e_barkia__code_e_barkia"]

# ---------------------------------------------------------------------------
# Inscription : action personnalisée pour approbation
# ---------------------------------------------------------------------------

@admin.action(description="Approuver les inscriptions sélectionnées")
def approuver_inscriptions(modeladmin, request, queryset):
    """Crée un utilisateur + client moral et envoie les identifiants."""
    for inscription in queryset.filter(is_approved=False):
        # Si l'utilisateur existe déjà on passe
        if User.objects.filter(username=inscription.email).exists():
            modeladmin.message_user(
                request,
                f"L'utilisateur {inscription.email} existe déjà.",
                level=messages.WARNING,
            )
            continue

        # Création de l'utilisateur
        password = get_random_string(length=10)
        user = User.objects.create_user(
            username=inscription.email,
            email=inscription.email,
            password=password,
        )

        # Création du client moral lié
        ClientMoral.objects.create(
            user=user,
            ice=inscription.ice,
            intitulé=inscription.intitulé,
            type=inscription.type,
            adresse=inscription.rue,
            ville=inscription.ville,
            quartier=inscription.quartier,
            gsm=inscription.gsm,
            email=inscription.email,
        )

        # Marquage comme approuvé
        inscription.is_approved = True
        inscription.save(update_fields=["is_approved"])

        # Envoi de l'e-mail d'activation
        send_mail(
            subject="Votre compte e-Barkia a été approuvé",
            message=(
                f"Bonjour {inscription.intitulé},\n\n"
                f"Votre compte a été validé. Voici vos identifiants :\n\n"
                f"Email : {inscription.email}\n"
                f"Mot de passe : {password}\n\n"
                "Pensez à changer votre mot de passe après votre première connexion."
            ),
            from_email="admin@ebarkia.com",
            recipient_list=[inscription.email],
            fail_silently=False,
        )

        modeladmin.message_user(
            request,
            f"Inscription {inscription.email} approuvée et email envoyé.",
            level=messages.SUCCESS,
        )


@admin.register(Inscription)
class InscriptionAdmin(admin.ModelAdmin):
    list_display = ("email", "ice", "intitulé", "is_approved")
    list_filter = ("is_approved", "type")
    actions = [approuver_inscriptions]

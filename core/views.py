from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils.timezone import now
from django.db.models import Count
from django.db import transaction
from django.conf import settings
from django.core.mail import send_mail
from datetime import timedelta
from django.urls import reverse
import logging

from core.models import (
    E_Barkia,
    Quartier,
    Ville,
    Inscription,
    ClientMoral,
)
from core.forms import InscriptionForm

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tableau de bord Administrateur
# ---------------------------------------------------------------------------
@staff_member_required
def admin_dashboard(request):
    """Tableau de bord principal pour les statistiques des e‐barkias."""
    today = now().date()
    last_7_days = [today - timedelta(days=i) for i in range(6, -1, -1)]

    daily_counts = (
        E_Barkia.objects
        .filter(date_envoi__in=last_7_days)
        .values('date_envoi')
        .annotate(count=Count('id'))
    )
    count_map = {entry['date_envoi']: entry['count'] for entry in daily_counts}

    context = {
        'total': E_Barkia.objects.count(),
        'declares': E_Barkia.objects.filter(statut='Déclaré').count(),
        'prises_en_charge': E_Barkia.objects.filter(statut='Prise en charge').count(),
        'distribues': E_Barkia.objects.filter(statut='Distribué').count(),
        'livres': E_Barkia.objects.filter(statut='Livrée').count(),
        'chart_labels': [str(day) for day in last_7_days],
        'chart_data': [count_map.get(day, 0) for day in last_7_days],
        'pending_count': Inscription.objects.filter(is_approved=False).count(),
    }
    return render(request, 'admin/admin_dashboard.html', context)

# ---------------------------------------------------------------------------
# Gestion des inscriptions
# ---------------------------------------------------------------------------
@staff_member_required
def pending_inscriptions(request):
    """Liste des inscriptions en attente de validation."""
    pendings = Inscription.objects.filter(is_approved=False)
    return render(request, 'admin/pending_inscriptions.html', {'pendings': pendings})


@staff_member_required
@transaction.atomic
def approve_inscription(request, inscription_id):
    """Valide une inscription, crée le compte utilisateur et envoie le mot de passe."""
    inscription = get_object_or_404(Inscription, pk=inscription_id, is_approved=False)

    # Génération d'un mot de passe aléatoire sécurisé
    password = User.objects.make_random_password()

    # Création de l'utilisateur
    user = User.objects.create_user(
        username=inscription.email,
        email=inscription.email,
        password=password,
        is_active=True,
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

    # Marque l'inscription comme approuvée
    inscription.is_approved = True
    inscription.save(update_fields=["is_approved"])

    # Envoi de l'e‑mail contenant le mot de passe
    try:
        login_url = request.build_absolute_uri(reverse('login'))
        send_mail(
            subject="Validation de votre compte E‑Barkia",
            message=(
                f"Bonjour {inscription.intitulé},\n\n"
                f"Votre compte a été validé par l'administrateur.\n"
                f"Vous pouvez dès à présent vous connecter avec les identifiants suivants :\n\n"
                f"Email : {inscription.email}\n"
                f"Mot de passe : {password}\n\n"
                f"Page de connexion : {login_url}\n\n"
                "Pensez à modifier votre mot de passe après la première connexion.\n\n"
                "Cordialement,\nL'équipe E‑Barkia"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[inscription.email],
            fail_silently=False,
        )
    except Exception as exc:
        logger.error("Erreur lors de l'envoi du mail d'activation : %s", exc)
        messages.warning(
            request,
            "L'inscription a été approuvée mais l'e‑mail n'a pas pu être envoyé. \n"
            "Veuillez vérifier la configuration SMTP.",
        )
    else:
        messages.success(request, f"Inscription {inscription.email} approuvée avec succès.")

    return redirect('pending_inscriptions')

# ---------------------------------------------------------------------------
# Vue d'inscription (côté public)
# ---------------------------------------------------------------------------
def signup_view(request):
    """Affiche le formulaire d'inscription et enregistre la demande."""
    if request.method == 'POST':
        form = InscriptionForm(request.POST)
        if form.is_valid():
            form.save()
            return render(request, 'core/confirmation.html')
    else:
        form = InscriptionForm()

    villes = Ville.objects.all()
    return render(request, 'core/login.html', {
        'villes': villes,
        'form': form,
    })

# ---------------------------------------------------------------------------
# Vue de connexion
# ---------------------------------------------------------------------------
def login_view(request):
    """Connexion pour les utilisateurs approuvés."""
    if request.method == 'POST':
        email = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)

        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Identifiants incorrects ou compte non approuvé.")

    return render(request, 'core/login.html', {
        'villes': Ville.objects.all(),
        'form': InscriptionForm(),
    })

# ---------------------------------------------------------------------------
# Endpoints AJAX HTMX
# ---------------------------------------------------------------------------
def load_quartiers(request):
    ville_id = request.GET.get('ville_id')
    quartiers = Quartier.objects.filter(ville_id=ville_id).values('id', 'nom')
    return JsonResponse(list(quartiers), safe=False)


def get_ville_from_quartier(request):
    quartier_id = request.GET.get('quartier_id')
    try:
        quartier = Quartier.objects.get(id=quartier_id)
        return JsonResponse({'ville_id': quartier.ville.id})
    except Quartier.DoesNotExist:
        return JsonResponse({}, status=404)

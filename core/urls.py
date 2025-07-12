from django.urls import path
from . import views

urlpatterns = [
    # ---------------------------------------------------------------------
    # Tableau de bord administrateur & gestion des inscriptions
    # ---------------------------------------------------------------------
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/inscriptions/', views.pending_inscriptions, name='pending_inscriptions'),
    path('admin/inscriptions/<int:inscription_id>/approve/', views.approve_inscription, name='approve_inscription'),

    # ---------------------------------------------------------------------
    # Authentification & inscription côté public
    # ---------------------------------------------------------------------
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),

    # ---------------------------------------------------------------------
    # Endpoints AJAX (HTMX)
    # ---------------------------------------------------------------------
    path('load-quartiers/', views.load_quartiers, name='load_quartiers'),
    path('get-ville-from-quartier/', views.get_ville_from_quartier, name='get_ville_from_quartier'),
    # autres routes...
    path('e-barkia/editeur/', views.editeur_telegramme, name='editeur_telegramme'),
]




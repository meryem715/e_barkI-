from django.db import models
from django.utils.timezone import now
from django.contrib.auth.models import User

# ---------------------
# Ville
# ---------------------
class Ville(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    code_postal = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.nom} ({self.code_postal})"


# ---------------------
# Quartier
# ---------------------
class Quartier(models.Model):
    nom = models.CharField(max_length=100)
    ville = models.ForeignKey(Ville, on_delete=models.CASCADE, related_name='quartiers')
    code_postal = models.CharField(max_length=10, blank=True)

    class Meta:
        unique_together = ('nom', 'ville')

    def __str__(self):
        return f"{self.nom} ({self.ville.nom})"


# ---------------------
# TypeE_Barkia
# ---------------------
class TypeE_Barkia(models.Model):
    nom = models.CharField(max_length=50, unique=True)
    mise_en_page = models.TextField(help_text="Instructions ou contenu HTML de mise en page propre à ce type")

    def __str__(self):
        return self.nom

# ---------------------
# Inscription
# ---------------------
class Inscription(models.Model):
    INTITULE_CHOICES = [
        ('Entreprise', 'Entreprise'),
        ('Association', 'Association'),
        ('Société', 'Société'),
        ('Administration', 'Administration'),
    ]
    email = models.EmailField(unique=True)
    ice = models.CharField(max_length=15, unique=True)
    intitulé = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=INTITULE_CHOICES)
    gsm = models.CharField(max_length=20)
    rue = models.CharField(max_length=255)
    ville = models.ForeignKey(Ville, on_delete=models.SET_NULL, null=True, blank=True)
    quartier = models.ForeignKey(Quartier, on_delete=models.SET_NULL, null=True, blank=True)
    is_approved = models.BooleanField(default=False)
    date_inscription = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.email} - {self.ice} - {'Approuvé' if self.is_approved else 'En attente'}"


# ---------------------
# ClientMoral
# ---------------------
class ClientMoral(models.Model):
    INTITULE_CHOICES = [
        ('Entreprise', 'Entreprise'),
        ('Association', 'Association'),
        ('Société', 'Société'),
        ('Administration', 'Administration'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="client_moral")
    ice = models.CharField(max_length=15, primary_key=True, unique=True)
    intitulé = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=INTITULE_CHOICES)
    adresse = models.CharField(max_length=255)
    ville = models.ForeignKey(Ville, on_delete=models.SET_NULL, null=True, blank=True, related_name='organisations')
    quartier = models.ForeignKey(Quartier, on_delete=models.SET_NULL, null=True, blank=True, related_name='organisations')
    gsm = models.CharField(max_length=20)
    email = models.EmailField()

    def __str__(self):
        return f"{self.ice} - {self.intitulé}"

# ---------------------
# Personnel
# ---------------------
class Personnel(models.Model):
    POSTE_CHOICES = [
        ('Agent', 'Agent Guichet'),
        ('Admin', 'Administrateur'),
    ]

    cin = models.CharField(max_length=10, primary_key=True)
    nom = models.CharField(max_length=50)
    prénom = models.CharField(max_length=50)
    email = models.EmailField()
    poste = models.CharField(max_length=20, choices=POSTE_CHOICES)
    adresse = models.CharField(max_length=255)
    téléphone = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.nom} {self.prénom} ({self.poste})"

# ---------------------
# E_Barkia
# ---------------------
class E_Barkia(models.Model):
    TYPE_CHOICES = [
        ('Urgent', 'Urgent'),
        ('Normal', 'Normal'),
    ]

    client = models.ForeignKey(ClientMoral, on_delete=models.CASCADE, related_name='ebarkia')
    code_e_barkia = models.CharField(max_length=50, unique=True, editable=False)
    contenu = models.TextField()
    objet = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    type_format = models.ForeignKey(TypeE_Barkia, on_delete=models.SET_NULL, null=True, blank=True, related_name='e_barkias')
    date_envoi = models.DateField(auto_now_add=True)
    heure_envoi = models.TimeField(auto_now_add=True)
    STATUT_CHOICES = [
        ('Déclaré', 'Déclaré'),
        ('Prise en charge', 'Prise en charge'),
        ('Distribué', 'Distribué'),
        ('Livrée', 'Livrée'),
    ]
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='Déclaré')
    intitulé_destinataire = models.CharField(max_length=100)
    adresse_destinataire = models.CharField(max_length=255)
    ville_destinataire = models.ForeignKey(Ville, on_delete=models.SET_NULL, null=True, blank=True, related_name='e_barkia_ville')
    quartier_destinataire = models.ForeignKey(Quartier, on_delete=models.SET_NULL, null=True, blank=True, related_name='e_barkia_quartier')
    nbre_caractere = models.PositiveIntegerField(default=0, editable=False)
    compteur = models.PositiveIntegerField(default=1)

    def save(self, *args, **kwargs):
        if not self.code_e_barkia:
            timestamp = now().strftime("%Y%m%d-%H%M%S")
            compteur = E_Barkia.objects.filter(client=self.client, date_envoi=self.date_envoi).count() + 1
            self.code_e_barkia = f"EB-{self.client.ice}-{self.date_envoi}-{timestamp}-{compteur}"
        self.nbre_caractere = len(self.contenu)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.objet} ({self.type}) - {self.statut}"

# ---------------------
# Livraison
# ---------------------
class Livraison(models.Model):
    e_barkia = models.OneToOneField(E_Barkia, on_delete=models.CASCADE, related_name='livraison')
    employé = models.ForeignKey(Personnel, on_delete=models.CASCADE, limit_choices_to={'poste': 'Agent'})
    date_livraison = models.DateField()
    heure_livraison = models.TimeField()
    cin_destinataire = models.CharField(max_length=10)

    def __str__(self):
        return f"Livraison de {self.e_barkia.objet} par {self.employé.nom}"

# ---------------------
# Prix
# ---------------------
class Prix(models.Model):
    prix_par_lettre = models.DecimalField(max_digits=6, decimal_places=2)
    date_effet = models.DateField()

    def __str__(self):
        return f"{self.prix_par_lettre} MAD (depuis {self.date_effet})"

# ---------------------
# Paiement
# ---------------------
class Paiement(models.Model):
    e_barkia = models.OneToOneField(E_Barkia, on_delete=models.CASCADE, related_name='paiement')
    montant = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    date_paiement = models.DateField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.e_barkia and self.e_barkia.nbre_caractere:
            try:
                prix_lettre = Prix.objects.latest('date_effet').prix_par_lettre
            except Prix.DoesNotExist:
                prix_lettre = 1.00  # valeur par défaut
            n_lettres = self.e_barkia.nbre_caractere // 30 + (1 if self.e_barkia.nbre_caractere % 30 else 0)
            self.montant = n_lettres * prix_lettre * self.e_barkia.compteur
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Paiement {self.montant} MAD pour {self.e_barkia.code_e_barkia}"

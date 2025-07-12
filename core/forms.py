from django import forms
from core.models import Inscription, Quartier, Ville

class InscriptionForm(forms.ModelForm):
    class Meta:
        model = Inscription
        fields = ['ice', 'intitulé', 'type', 'email', 'gsm', 'ville', 'quartier', 'rue']
        widgets = {
            'type': forms.Select(attrs={'class': 'form-select'}),
            'ville': forms.Select(attrs={'class': 'form-select','hx-get': '/load-quartiers/','hx-target': '#id_quartier','hx-trigger': 'change'}),
            'quartier': forms.Select(attrs={'class': 'form-select'}),
            'rue': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['quartier'].queryset = Quartier.objects.none()

        if 'ville' in self.data:
            try:
                ville_id = int(self.data.get('ville'))
                self.fields['quartier'].queryset = Quartier.objects.filter(ville_id=ville_id).order_by('nom')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.ville:
            self.fields['quartier'].queryset = self.instance.ville.quartiers.order_by('nom')


class LoginForm(forms.Form):
    username = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={
        'placeholder': 'Email',
        'class': 'form-control'
    }))
    password = forms.CharField(label='Mot de passe', widget=forms.PasswordInput(attrs={
        'placeholder': 'Mot de passe',
        'class': 'form-control'
    }))

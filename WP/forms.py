from django.forms import ModelForm, PasswordInput,HiddenInput
from django.contrib.auth.forms import UserCreationForm
from .models import WaterPlantLoc,WaterPlant,User

class WaterPlantLocForm(ModelForm):

    class Meta:
        model=WaterPlantLoc
        fields=['district','mandal','gram_panchayat','village','constency']


class InchargeForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['name','username', 'first_name', 'last_name', 'password1', 'password2','number']
        widgets ={ 'name': HiddenInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].required = False
        
    def clean(self):
        self.cleaned_data = super().clean()
        self.cleaned_data['name'] = self.cleaned_data['first_name'] +' '+ self.cleaned_data['last_name']
        return self.cleaned_data






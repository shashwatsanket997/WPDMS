from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractUser
from django.urls import reverse, reverse_lazy

# Create your models here.


class WarrentyYear(models.Model):
    year = models.IntegerField()

 # District model


class WaterPlantLoc(models.Model):
    district = models.CharField(max_length=200)
    mandal = models.CharField(max_length=200)
    gram_panchayat = models.CharField(max_length=200)
    village = models.CharField(max_length=200)
    constency = models.CharField(max_length=200)

    def __str__(self):
        return self.district+' | '+self.mandal+' | ' + self.gram_panchayat+' | '+self.village+' | '+self.constency


class User(AbstractUser):
    mob_no_regex = RegexValidator(regex='^\([0-9]{2}\)[1-9][0-9]{9}$|^[1-9][0-9]{9}$',
                                  message="Should be of 10 digits like (91)9999999999 or 9999999999")
    name = models.CharField(max_length=100, verbose_name='Incharge Name')
    number = models.CharField(max_length=10)

    def __str__(self):
        return self.username

    def get_absolute_url(self):
        return reverse_lazy('WP:CreateWaterPlant')


TYPE_CHOICES = (
    ('Foundation', 'FOUNDATION'),
    ('MPLADS', 'MPLADS'),
)


class WaterPlant(models.Model):
    loc = models.ForeignKey(
        WaterPlantLoc, on_delete=models.CASCADE, default='0')
    populations = models.CharField(max_length=200, null=True, blank=True)
    phone_regex = RegexValidator(
        regex=r'^\d{10}$', message="Phone number should be up to 10 digits only")
    capacity = models.CharField(max_length=10, blank=True, null=True)
    date = models.DateField()
    contact_person = models.CharField(max_length=200)
    contact_number = models.CharField(validators=[phone_regex], max_length=10)
    operator_name = models.CharField(max_length=200)
    operator_phone_number = models.CharField(
        validators=[phone_regex], max_length=10)
    incharge = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.DO_NOTHING)
    plant_type = models.CharField(
        choices=TYPE_CHOICES, max_length=15, null=True, blank=True)
    is_amc = models.BooleanField(default=False)

    def __str__(self):
        return self.loc.village


class Consumables(models.Model):
    WP = models.ForeignKey(WaterPlant, on_delete=models.CASCADE)
    filters = models.CharField(max_length=5)
    liquid_case = models.CharField(max_length=5)
    date = models.DateField()


class Cost(models.Model):
    filters = models.CharField(max_length=5)
    liquid = models.CharField(max_length=5)
    date = models.DateField()


class repair_parts(models.Model):
    WP = models.ForeignKey(WaterPlant, on_delete=models.CASCADE)
    parts = models.CharField(max_length=100)
    description = models.TextField(max_length=600)
    date = models.DateField()
    amount = models.CharField(max_length=10)

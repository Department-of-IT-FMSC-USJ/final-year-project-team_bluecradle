from django.db import models
from accounts_module.models import PHM_User

class Infant(models.Model):
    SEX_CHOICES = [
        ('M','Male'),
        ('F','Female'),
    ]

    # PHN is the primary key - retrieved from the physical CHDR booklet
    # Parents use this exact value to self-register on the portal.
    phn = models.CharField(max_length=20, primary_key=True)

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    full_name = models.CharField(max_length=200)
    date_of_birth = models.DateField()
    sex = models.CharField(max_length=1, choices=SEX_CHOICES)

    # Birth anthropometrics — static features fed into the ML model.
    birth_weight_kg = models.DecimalField(max_digits=4, decimal_places=2)
    birth_length_cm = models.DecimalField(max_digits=4, decimal_places=1)
    birth_order = models.PositiveSmallIntegerField() # which child this infant is in the family. 1 = firstborn, 2 = second child, and so on. It's a static ML feature because firstborn infants and higher birth-order infants in large families show statistically different malnutrition risk profiles.

    # The PHM who registered this infant.
    # PROTECT prevents accidental PHM deletion from wiping clinical records.
    registered_phm = models.ForeignKey(
        PHM_User,
        on_delete=models.PROTECT,
        related_name='registered_infants'
    )

    # Denormalized copy of the PHM's division at registration time.
    # Copied here so future MOH-level GROUP BY queries need no JOIN.
    moh_division = models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.phn})'
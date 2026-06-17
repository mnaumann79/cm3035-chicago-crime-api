from django.db import models


class OffenseCategory(models.Model):
    CATEGORY_CHOICES = [
        ('violent', 'Violent'),
        ('property', 'Property'),
        ('quality_of_life', 'Quality of Life'),
    ]

    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)

    class Meta:
        verbose_name_plural = 'Offense categories'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.code})'


class District(models.Model):
    AREA_CHOICES = [
        ('police', 'Police District'),
        ('community', 'Community Area'),
    ]

    district_num = models.IntegerField(unique=True)
    name = models.CharField(max_length=100)
    area_type = models.CharField(max_length=20, choices=AREA_CHOICES)
    population = models.IntegerField(default=0)

    class Meta:
        ordering = ['district_num']

    def __str__(self):
        return f'District {self.district_num} — {self.name}'


class Incident(models.Model):
    case_number = models.CharField(max_length=20, unique=True)
    date = models.DateTimeField()
    block = models.CharField(max_length=200)
    arrest = models.BooleanField(default=False)
    domestic = models.BooleanField(default=False)
    fbi_code = models.CharField(max_length=10)
    primary_type = models.ForeignKey(
        OffenseCategory,
        on_delete=models.CASCADE,
        related_name='incidents',
    )
    district = models.ForeignKey(
        District,
        on_delete=models.CASCADE,
        related_name='incidents',
    )

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f'{self.case_number} — {self.primary_type.name}'

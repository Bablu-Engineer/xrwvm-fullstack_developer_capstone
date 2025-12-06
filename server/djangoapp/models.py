from django.db import models
# 'now' is imported but not used, so we remove it
from django.core.validators import MaxValueValidator, MinValueValidator


class CarMake(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    # Optional fields
    country = models.CharField(max_length=100, blank=True, null=True)
    established_year = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.name


class CarModel(models.Model):
    # Many-to-one relationship to CarMake
    car_make = models.ForeignKey(CarMake, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    CAR_TYPES = [
        ('SEDAN', 'Sedan'),
        ('SUV', 'SUV'),
        ('WAGON', 'Wagon'),
        ('TRUCK', 'Truck'),
        ('COUPE', 'Coupe'),
    ]

    type = models.CharField(max_length=20, choices=CAR_TYPES, default='SUV')

    year = models.IntegerField(
        default=2023,
        validators=[
            MaxValueValidator(2023),
            MinValueValidator(2015),
        ],
    )

    # dealer ID from Cloudant database
    dealer_id = models.IntegerField(default=0)
    # Optional fields
    color = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.car_make.name} {self.name} ({self.year})"

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

class MerchantManager(BaseUserManager):
    def create_user(self, email, name, password=None):
        if not email:
            raise ValueError('Merchants must have an email address')
        merchant = self.model(email=self.normalize_email(email), name=name)
        merchant.set_password(password)
        merchant.save(using=self._db)
        return merchant

    def create_superuser(self, email, name, password=None):
        merchant = self.create_user(email, name, password)
        merchant.is_admin = True
        merchant.save(using=self._db)
        return merchant

class Merchant(AbstractBaseUser):
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = MerchantManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.is_admin

class Ware(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.FloatField()
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
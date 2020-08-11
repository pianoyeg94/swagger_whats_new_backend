from django.db import models


class SingletonModel(models.Model):
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs) -> None:
        self.pk = 1
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs) -> None:
        pass
    
    @classmethod
    def load(cls) -> models.Model:
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

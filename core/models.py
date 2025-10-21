from django.db import models
from django.utils import timezone

# Create your models here.





class UiWikiComponent(models.Model):
    id = models.AutoField(primary_key=True)
    nome = models.CharField("nome", max_length=255)
    categoria = models.CharField("categoria", max_length=100, blank=True)
    link_figma = models.TextField("link_figma", blank=True)
    autor = models.CharField("autor", max_length=100, blank=True)
    tags = models.TextField("tags", blank=True, help_text="Tags separadas por vírgula")
    thumbnail_url = models.TextField("thumbnail_url", blank=True)
    data_importacao = models.DateTimeField("data_importacao", default=timezone.now)

    class Meta:
        verbose_name = "Componente UIWiki"
        verbose_name_plural = "Componentes UIWiki"
        ordering = ["-data_importacao"]

    def __str__(self):
        return self.nome or f"Componente #{self.pk}"

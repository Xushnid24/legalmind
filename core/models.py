from django.db import models

class Case(models.Model):
    title = models.CharField(
        max_length=255,
        verbose_name="Название дела",
        help_text="Введите короткое название судебного дела"
    )
    text = models.TextField(
        verbose_name="Текст дела",
        help_text="Введите полный текст судебного дела"
    )
    date = models.DateField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )

    def __str__(self):
        return self.title


class GeneratedDocument(models.Model):
    doc_type = models.CharField(
        max_length=100,
        verbose_name="Тип документа",
        help_text="Укажите тип документа (например: иск, ходатайство, заключение)"
    )
    text = models.TextField(
        verbose_name="Текст документа",
        help_text="Сюда будет помещён сгенерированный текст документа"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )

    def __str__(self):
        return f"{self.doc_type} ({self.created_at.strftime('%Y-%m-%d')})"

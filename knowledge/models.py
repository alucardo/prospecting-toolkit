from django.db import models
from django.contrib.auth.models import User
import re


class KnowledgeSettings(models.Model):
    video_folder_url = models.URLField(
        blank=True,
        verbose_name='Link do folderu wideo na Google Drive',
        help_text='Link do folderu na Google Drive z inspiracjami wideo',
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Ustawienia bazy wiedzy'

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return 'Ustawienia bazy wiedzy'


class KnowledgeTag(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Nazwa')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Tag'
        verbose_name_plural = 'Tagi'

    def __str__(self):
        return self.name


class VideoInspiration(models.Model):
    title = models.CharField(max_length=255, verbose_name='Tytuł')
    drive_url = models.URLField(verbose_name='Link do Google Drive')
    description = models.TextField(blank=True, verbose_name='Opis / przemyślenia')
    tags = models.ManyToManyField(
        KnowledgeTag,
        blank=True,
        related_name='videos',
        verbose_name='Tagi',
    )
    created_by = models.ForeignKey(
        User,
        null=True,
        on_delete=models.SET_NULL,
        related_name='video_inspirations',
        verbose_name='Dodano przez',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Inspiracja wideo'
        verbose_name_plural = 'Inspiracje wideo'

    def __str__(self):
        return self.title

    @property
    def drive_file_id(self):
        """Wyciąga FILE_ID z linku Google Drive."""
        match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', self.drive_url)
        return match.group(1) if match else None

    @property
    def drive_preview_url(self):
        """URL do osadzonego odtwarzacza wideo."""
        fid = self.drive_file_id
        return f'https://drive.google.com/file/d/{fid}/preview' if fid else None

    @property
    def drive_thumbnail_url(self):
        """URL do miniatury (statyczny obrazek)."""
        fid = self.drive_file_id
        return f'https://drive.google.com/thumbnail?id={fid}&sz=w400' if fid else None

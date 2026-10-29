from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import SelectionAttachment


@receiver(post_delete, sender=SelectionAttachment)
def delete_attachment_file(sender, instance, using, **kwargs):
    # Also clean up files when a selection or project is deleted, after commit.
    storage, name = instance.file.storage, instance.file.name
    if name:
        transaction.on_commit(lambda: storage.delete(name), using=using)

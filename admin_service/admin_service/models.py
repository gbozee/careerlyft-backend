from django.db import models


class QuickbookStorage(models.Model):
    token = models.TextField()
    # Field name made lowercase.
    realmid = models.CharField(
        db_column='realmId', max_length=200, blank=True, null=True)
    date_added = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'quickbooks_quickbooksstorage'

from django.db import models


class Guide(models.Model):
	class Meta:
		ordering = ('name',)

	GUIDE_TYPES = (
		('BT', 'Til bartendere'),
		('BM', 'Til bestyrelsesmedlemmer'),
		('ALL', 'Til alle'),
	)

	name = models.CharField(max_length=256)
	category = models.CharField(max_length=3, choices=GUIDE_TYPES)
	document = models.FileField(upload_to='guides/')

	def __str__(self):
		return self.name

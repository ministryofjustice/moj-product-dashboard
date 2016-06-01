from datetime import date
from dashboard.apps.prototype import models

jn = models.Person.objects.get(name='James Narey')
jr = models.Person.objects.get(name='Josh Rowe')
cx = models.Person.objects.get(name='Cliff Xuan')

tdy = date.today()


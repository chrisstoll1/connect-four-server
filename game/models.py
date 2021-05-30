from django.db import models
from django.db.models.fields import BooleanField, CharField, IntegerField, TextField

# Create your models here.
class Board(models.Model):
    boxes = TextField()
    roomName = CharField(max_length=100)
    redConnected = BooleanField(default=False)
    redPlayer = CharField(max_length=200, default="")
    yellowConnected = BooleanField(default=False)
    yellowPlayer = CharField(max_length=200, default="")
    colorFlag = BooleanField(default=False)
    winner = BooleanField(default=False)

    def __str__(self):
        return self.roomName
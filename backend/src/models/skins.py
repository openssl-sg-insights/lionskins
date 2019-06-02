# -*- coding: utf-8 -*-

from datetime import date, datetime

from slugify import slugify

from ..init import db
from ..models.enums import Apps
from .history import History
from .model_mixin import ModelMixin
from .prices import Price


class Skin(ModelMixin, db.Document):

    _app = db.StringField(db_field="app", choices=Apps, required=True)
    slug = db.StringField(required=True)

    name = db.StringField(required=True)
    image_url = db.URLField()
    creation_date = db.DateTimeField(required=True, default=datetime.now)

    prices = db.EmbeddedDocumentListField(Price)

    meta = {
        'indexes': ['_app', 'slug', 'name'],
        'allow_inheritance': True,
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.slug = self.generate_slug()

    def __repr__(self):
        return f'<Skin id={self.id}, name={self.name}>'

    def __str__(self):
        return f'<Skin {self.id} - {self.name}>'

    @property
    def fullname(self):
        return self.name

    def generate_slug(self):
        return slugify(self.name)

    @property
    def app(self):
        return Apps[self._app]

    @app.setter
    def app(self, value):
        self._app = value.name

    def add_price(self, provider, price):
        now = datetime.now()
        for price_ in self.prices:
            if price_.provider == provider:
                price_.price = price
                price_.update_date = now
                break
        else:
            self.prices.append(Price(price=price, provider=provider))

        try:
            history = History.get(skin=self.id, provider=provider, creation_date__gte=date.today())
        except History.DoesNotExist:
            History.create(skin=self.id, provider=provider, price=price)
        except History.MultipleObjectsReturned:
            pass
        else:
            if history.price > price:
                history.price = price
                history.creation_date = now
                history.save()
        self.save()

# -*- coding: utf-8 -*-
from rest_framework import serializers

from .models import Person, Product


class PersonSerializer(serializers.ModelSerializer):

    class Meta:
        model = Person
        exclude = ['raw_data']


class PersonProductSerializer(serializers.ModelSerializer):

    time_spent = serializers.SerializerMethodField()

    def get_time_spent(self, obj):
        person = self.context['person']
        start_date = self.context['start_date']
        end_date = self.context.get('end_date')
        days = person.time_on_product(obj, start_date, end_date)
        return {
            'from': start_date,
            'to': end_date,
            'days': days
        }

    class Meta:
        model = Product
        fields = ['id', 'name', 'time_spent']

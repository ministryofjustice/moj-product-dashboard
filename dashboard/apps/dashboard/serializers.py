# -*- coding: utf-8 -*-
from rest_framework import serializers

from .models import Person, Product, Department, Skill


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


class SkillSerializer(serializers.ModelSerializer):

    persons = serializers.SerializerMethodField()

    def get_persons(self, instance):
        return PersonSerializer(
            instance.persons.filter(is_current=True),
            read_only=True,
            many=True
        ).data

    class Meta:
        model = Skill
        fields = ['id', 'name', 'persons']


class DepartmentSerializer(serializers.ModelSerializer):

    persons = serializers.SerializerMethodField()

    def get_persons(self, instance):
        return PersonSerializer(
            instance.persons.filter(is_current=True),
            read_only=True,
            many=True
        ).data

    class Meta:
        model = Department
        fields = ['id', 'name', 'float_id', 'persons']


class PersonSerializer(serializers.ModelSerializer):

    department = serializers.SlugRelatedField(
        read_only=True, slug_field='name')
    skills = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field='name')

    class Meta:
        model = Person
        exclude = ['raw_data']

# -*- coding: utf-8 -*-
from datetime import datetime
from collections import OrderedDict

from django.shortcuts import render, redirect
from django.http import Http404, HttpResponse
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import viewsets, generics

from dashboard.libs.date_tools import parse_date
from dashboard.libs import swagger_tools
from .models import Product, Area, ProductGroup, Person, Department
from .tasks import sync_float
from .serializers import (
    PersonSerializer, PersonProductSerializer, DepartmentSerializer,
    DepartmentWithPersonsSerializer)
from . import spreadsheets


def _product_meta(request, product):
    meta = {
        'can_edit': product.can_user_change(request.user),
        'admin_url': request.build_absolute_uri(product.admin_url)
    }
    return meta


def product_html(request, id):
    if not id:
        id = Product.objects.visible().first().id
        return redirect(reverse(product_html, kwargs={'id': id}))
    try:
        Product.objects.visible().get(id=id)
    except (ValueError, Product.DoesNotExist):
        raise Http404
    return render(request, 'common.html')


@api_view(['GET'])
def product_json(request, id):
    """
    detail view of a single product
    """
    request_data = request.GET
    try:
        product = Product.objects.visible().get(id=id)
    except (ValueError, Product.DoesNotExist):
        error = 'cannot find product with id={}'.format(id)
        return Response({'error': error}, status=404)

    start_date = request_data.get('startDate')
    if start_date:
        start_date = parse_date(start_date)
    end_date = request_data.get('endDate')
    if end_date:
        end_date = parse_date(end_date)
    # get the profile of the product for each month
    profile = product.profile(
        start_date=start_date,
        end_date=end_date,
        freq='MS',
        calculation_start_date=settings.PEOPLE_COST_CALCATION_STARTING_POINT
    )
    meta = _product_meta(request, product)
    return Response({**profile, 'meta': meta})


def product_group_html(request, id):
    if not id:
        id = ProductGroup.objects.first().id
        return redirect(reverse(product_group_html, kwargs={'id': id}))
    try:
        ProductGroup.objects.get(id=id)
    except (ValueError, ProductGroup.DoesNotExist):
        raise Http404
    return render(request, 'common.html')


@api_view(['GET'])
def product_group_json(request, id):
    """
    detail view of a single product group
    """
    # TODO handle errors
    try:
        product_group = ProductGroup.objects.get(id=id)
    except (ValueError, ProductGroup.DoesNotExist):
        error = 'cannot find product group with id={}'.format(id)
        return Response({'error': error}, status=404)

    # get the profile of the product group for each month
    profile = product_group.profile(
        freq='MS',
        calculation_start_date=settings.PEOPLE_COST_CALCATION_STARTING_POINT)
    meta = _product_meta(request, product_group)
    return Response({**profile, 'meta': meta})


class PersonViewSet(viewsets.ReadOnlyModelViewSet):
    """
    View set for person

    retrieve:
    Detail view of a single person

    list:
    List view of persons
    """
    queryset = Person.objects.all()
    serializer_class = PersonSerializer


@swagger_tools.additional_schema(
    OrderedDict([
        ('start_date', {
            'name': 'start_date',
            'required': False,
            'location': 'query',
            'type': 'string',
            'description': 'start date',
         }),
        ('end_date', {
            'name': 'end_date',
            'required': False,
            'location': 'query',
            'type': 'string',
            'description': 'end date',
         }),
    ])
)
class PersonProductListView(generics.ListAPIView):
    """
    List view of products the person(id={person_id}) spends time on
    in the time window defined by start date and end date.
    """

    serializer_class = PersonProductSerializer

    def get_queryset(self):
        person = Person.objects.get(id=self.kwargs.get('person_id'))
        return person.products

    def get_serializer_context(self):
        context = super().get_serializer_context()
        start_date = self.request.query_params.get('start_date')
        if start_date:
            start_date = parse_date(start_date)
        end_date = self.request.query_params.get('end_date')
        if end_date:
            end_date = parse_date(end_date)
        return {
            'start_date': start_date,
            'end_date': end_date,
            'person': Person.objects.get(id=self.kwargs.get('person_id')),
            **context
        }


def service_html(request, id):
    if not id:
        id = Area.objects.filter(visible=True).first().id
        return redirect(reverse(service_html, kwargs={'id': id}))
    try:
        Area.objects.filter(visible=True).get(id=id)
    except (ValueError, Area.DoesNotExist):
        raise Http404
    return render(request, 'common.html')


@api_view(['GET'])
def service_json(request, id):
    """
    detail view of a single service area
    """
    try:
        area = Area.objects.filter(visible=True).get(id=id)
    except (ValueError, Area.DoesNotExist):
        error = 'cannot find service area with id={}'.format(id)
        return Response({'error': error}, status=404)
    # get the profile of the service
    profile = area.profile(
        calculation_start_date=settings.PEOPLE_COST_CALCATION_STARTING_POINT)
    return Response(profile)


def portfolio_html(request):
    return render(request, 'common.html', {'body_classes': 'portfolio'})


@api_view(['GET'])
def services_json(request):
    """
    list view of all service areas
    """
    result = [
        area.profile(
            calculation_start_date=settings.PEOPLE_COST_CALCATION_STARTING_POINT
        )
        for area in Area.objects.filter(visible=True)
    ]
    return Response(result)


@login_required
@api_view(['POST'])
def sync_from_float(request):
    """
    sync data from Float.com
    """
    sync_float.delay()
    return Response({
        'status': 'STARTED'
    })


@api_view(['GET'])
def products_spreadsheet(request, **kwargs):
    show = kwargs.get('show', 'visible')
    if show == 'visible':
        products = Product.objects.visible()
    elif show == 'all':
        products = Product.objects.all()
    else:
        products = Product.objects.filter(pk=show)
    spreadsheet = spreadsheets.Products(
        products, settings.PEOPLE_COST_CALCATION_STARTING_POINT
    )
    response = HttpResponse(content_type="application/vnd.ms-excel")
    response['Content-Disposition'] = 'attachment; filename={}_{}_{}.xlsx'.format(
        'ProductData', show, datetime.now().strftime('%Y-%m-%d_%H:%M:%S'))
    spreadsheet.workbook.save(response)
    return response


class DepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    View set for department

    retrieve:
    Detail view of a single department

    list:
    List view of departments
    """
    queryset = Department.objects.all()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return DepartmentWithPersonsSerializer
        return DepartmentSerializer

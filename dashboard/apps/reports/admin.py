# -*- coding: utf-8 -*-
from datetime import date
import re
from dateutil.relativedelta import relativedelta
from django.core.checks import messages
from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth.admin import csrf_protect_m
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.decorators import method_decorator
from dashboard.libs.rate_converter import last_date_in_month

from dashboard.apps.dashboard.permissions import FinancePermissions
from dashboard.apps.dashboard.models import Area

from .forms import PayrollUploadForm, ExportForm
from .models import ProductProxy


class ReportsAdmin(admin.ModelAdmin, FinancePermissions):

    def get_urls(self):
        urls = [
            url(
                r'^upload/$',
                self.admin_site.admin_view(self.upoload_view),
                name='person_upload_payroll'),
            url(
                r'^export/$',
                self.admin_site.admin_view(self.export_view),
                name='product_export'),
        ]
        return urls

    def has_upload_permission(self, request):
        return self.is_finance(request.user)

    def get_model_perms(self, request):
        perms = super(ReportsAdmin, self).get_model_perms(request)
        perms.update({
            'upload': self.has_upload_permission(request),
            'export': self.has_upload_permission(request),
        })
        return perms

    @csrf_protect_m
    @transaction.atomic
    @method_decorator(permission_required('reports.upload_payroll',
                                          raise_exception=True))
    def upoload_view(self, request, *args, **kwargs):
        if not self.has_upload_permission(request):
            raise PermissionDenied

        start = (date.today() - relativedelta(months=1)).replace(day=1)
        end = last_date_in_month(start)

        initial = {
            'date_range': (start, end)
        }

        if request.method == 'POST':
            form = PayrollUploadForm(data=request.POST, files=request.FILES,
                                     initial=initial)
            if form.is_valid():
                form.save()
                level = messages.INFO
                message = 'Successfully uploaded %s payroll' % form.month
            else:
                level = messages.ERROR
                message = 'Errors uploading %s payroll' % form.month

            self.message_user(request, message, level=level)
        else:
            form = PayrollUploadForm(initial=initial)

        context = self.admin_site.each_context(request)
        context.update({
            'opts': self.model._meta,
            'has_permission': self.is_finance(request.user),
            'form': form,
        })

        return render_to_response(
            'admin/dashboard/upload.html',
            context,
            context_instance=RequestContext(request))

    @csrf_protect_m
    @transaction.atomic
    @method_decorator(permission_required('reports.adjustment_export',
                                          raise_exception=True))
    def export_view(self, request):
        if not self.is_finance(request.user):  # pragma: no cover
            raise PermissionDenied

        start = (date.today() - relativedelta(months=1)).replace(day=1)
        end = last_date_in_month(start)

        initial = {
            'date_range': (start, end)
        }

        if request.method == 'POST':
            form = ExportForm(data=request.POST, files=request.FILES,
                              initial=initial)
            if form.is_valid():
                fname = '%s_%s_%s-%s.xlsm' % (
                    form.cleaned_data['export_type'],
                    re.sub(
                        '[^0-9a-zA-Z]+',
                        '-',
                        form.cleaned_data['product'].name),
                    form.cleaned_data['date_range'][0].year,
                    form.cleaned_data['date_range'][0].month)
                workbook = form.export()
                response = HttpResponse(
                    content_type="application/vnd.ms-excel")
                response['Content-Disposition'] = 'attachment; filename=%s' \
                                                  % fname
                workbook.save(response)
                return response
        else:
            form = ExportForm(initial=initial)

        context = self.admin_site.each_context(request)
        context.update({
            'opts': self.model._meta,
            'has_permission': self.is_finance(request.user),
            'form': form,
            'areas': Area.objects.exclude(products__isnull=True)
                        .order_by('name').prefetch_related('products'),
        })

        return render_to_response(
            'admin/dashboard/export.html',
            context,
            context_instance=RequestContext(request))


admin.site.register(ProductProxy, ReportsAdmin)

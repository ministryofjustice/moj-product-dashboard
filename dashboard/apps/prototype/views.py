import json
import random
from django.views.generic import View, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect


class Index(TemplateView):

    template_name = 'index.html'


class DataResponse(View):

    def get(self, request, *args, **kwargs):

        x_axis = ['January', 'February', 'March', 'April',
                  'May', 'June', 'July', 'August', 'September',
                  'October', 'November', 'December']

        y_axis = []

        for month in x_axis:

            y_axis.append(random.random() * 100)

        trace = {
            'x': x_axis,
            'y': y_axis,
            'type': 'bar',
        }

        data = [trace, ]

        return JsonResponse(data, safe=False)

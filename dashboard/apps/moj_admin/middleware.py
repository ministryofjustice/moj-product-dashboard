from django.shortcuts import render
from django.http import HttpResponse
from bs4 import BeautifulSoup
from django.conf import settings


class MoJAdminMiddleWare(object):

    def __init__(self):
        self.extra_css_files = [settings.STATIC_URL + 'moj_admin/styles/gov-uk-elements.css',
                                settings.STATIC_URL + 'moj_admin/styles/gov-uk-elements-moj-admin.css']
        self.moj_template_url = 'moj_admin.html'

    def process_response(self, request, response):

        if 'admin' in request.path:

            # return response
            # import ipdb; ipdb.set_trace()
            admin_doc = self.get_admin_doc(response)
            admin_elements = self.get_admin_elements(admin_doc)
            admin_scripts = admin_doc.find_all('script')
            added_styles = self.get_added_styles()

            moj_doc = self.get_moj_doc(request)
            moj_main_div = moj_doc.find(id='content')

            self.append_elements(moj_doc.body, admin_scripts)
            self.append_elements(moj_doc.head, added_styles)
            self.append_admin_elements(moj_main_div, admin_elements)

            response = HttpResponse(str(moj_doc))

        return response

    def append_admin_elements(self, target_element, element_dict):

        self.append_elements(target_element, element_dict['user_tools'])
        self.append_elements(target_element, element_dict['breadcrumbs'])
        self.append_elements(target_element, element_dict['object_tools'])
        self.append_elements(target_element, element_dict['actions'])
        self.append_elements(target_element, element_dict['modules'])
        self.append_elements(target_element, element_dict['results'])

    def get_admin_elements(self, document):

        admin_elements = {}
        admin_elements['user_tools'] = document.find_all(id='user-tools')
        admin_elements['breadcrumbs'] = self.get_elements_by_class(document, 'breadcrumbs')
        admin_elements['object_tools'] = self.get_elements_by_class(document, 'object-tools')
        admin_elements['actions'] = self.get_elements_by_class(document, 'actions')
        admin_elements['results'] = self.get_elements_by_class(document, 'results')
        admin_elements['modules'] = self.get_elements_by_class(document, 'module')

        return admin_elements

    def get_added_styles(self):
        temp_bs = BeautifulSoup('', 'lxml')
        added_styles = []
        for path in self.extra_css_files:
            # link_text = self.style_link_string(path)
            tag = temp_bs.new_tag('link', type='text/css', href=path, rel='stylesheet')
            added_styles.append(tag)
        return added_styles

    def get_elements_by_class(self, document, classname):
        elements = document.find_all(class_=classname)
        return elements

    def style_link_string(self, path):
        return '<link rel="stylesheet" type="text/css" href="%s" />' % path

    def get_style_links(self, document):
        styles = document.head.find_all('link')
        return styles

    def append_elements(self, target_element, elements):
        for element in elements:
            target_element.append(element)

    def insert_elements(self, target_element, elements):
        for element in reversed(elements):
            target_element.contents.insert(0, element)

    def get_admin_doc(self, response):
        admin_str = response.content.decode('utf-8')
        admin_doc = BeautifulSoup(admin_str, 'lxml')
        return admin_doc

    def get_moj_doc(self, request):
        moj_http_response = render(request, self.moj_template_url)
        moj_content_str = moj_http_response.content.decode('utf-8')
        moj_doc = BeautifulSoup(moj_content_str, 'lxml')
        return moj_doc

    def merge_pages(self, admin_doc, moj_doc):

        admin_styles = self.get_style_links(admin_doc)
        admin_main_div = admin_doc.find(id='content-main')

        moj_main_div = moj_doc.find(id='content')

        self.append_elements(moj_doc.head, admin_styles)

        moj_main_div.append(admin_main_div)

        return moj_doc

import pprint
import ipdb

class InterCept(object):

    def process_template_response(self, request, response):
        pprint.pprint(response.__dict__)
        # ipdb.set_trace()
        return response



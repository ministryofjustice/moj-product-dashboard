import pprint


class InterceptMiddleware(object):

    def process_response(self, request, response):
        pprint.pprint(response.__dict__)
        return response

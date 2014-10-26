import hmac
import hashlib
import time
import urllib2
import json

from tornado import escape, httpclient

class QueenBee(object):
	def __init__(self, api_key=None, api_secret=None):
		self.__api_key = api_key
		self.__api_secret = api_secret

		self.httpclient = httpclient.HTTPClient()

	def __nonce(self):
		return int(time.time() * 1000)

	def __signature(self, request):
		return hmac.new(self.__api_secret, request, digestmod=hashlib.sha256).hexdigest().lower()

	def api_call(self, method, request, query={}, body=None):
		if not request.startswith('/'):
			request = '/' + request

		request_params = {
			'method': method
		}

		query['nonce'] = self.__nonce()
		if query:
			params = '&'.join(['{0:s}={1:s}'.format(*map(escape.url_escape, map(str, param))) for param in query.items()])
			request = request + '?' + params

		url = "https://queenbee.webscript.io" + request

		if not body is None:
			request_params['body'] = json.dumps(body)

		request_params['headers'] = {
			'Key': self.__api_key,
			'Sign': self.__signature(request)
		}

		request = httpclient.HTTPRequest(url, **request_params)
		dir(request)

		response = self.httpclient.fetch(request)

		return response.body

	def heartbeat(self):
		return self.api_call('POST', '/v2/heartbeat', body={})

	def __get_callees(self):
		return self.api_call('GET', '/v2/callees')
	def __set_callees(self, callees):
		return self.api_call('POST', '/v2/callees', body=callees)
	callees = property(__get_callees, __set_callees)

	def __get_message(self):
		return self.api_call('GET', '/v2/status')
	def __set_message(self, message):
		return self.api_call('POST', '/v2/status', body={'message': message})
	message = property(__get_message, __set_message)


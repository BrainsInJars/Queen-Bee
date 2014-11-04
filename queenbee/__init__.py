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

	def _make_request(self, request, **query):
		if not request.startswith('/'):
			request = '/' + request

		def params(param):
			key, value = param
			if value is None:
				return

			key = escape.url_escape(str(key))
			value = escape.url_escape(str(value))

			return '{0:s}={1:s}' % (key, value)

		if query:
			request = request + '?' + '&'.join(filter(lambda p: not p is None, map(params, query.items()))

		return 'https://queenbee.webscript.io', request

	def twilio_endpoint(self, conference=None, voice='woman', message=None):
		endpoint, request = self._make_request('/v2/twilio', conference=conference, voice=voice, message=message)
		return endpoint + request

	def api_call(self, method, request, query={}, body=None):
		request_params = {
			'method': method
		}
		query['nonce'] = self.__nonce()

		endpoint, request = self._make_request(request, **query)
		url = endpoint + request

		if not body is None:
			request_params['body'] = json.dumps(body)

		request_params['headers'] = {
			'Key': self.__api_key,
			'Sign': self.__signature(request)
		}

		request = httpclient.HTTPRequest(url, **request_params)
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
		return self.api_call('GET', '/v2/message')
	def __set_message(self, message):
		return self.api_call('POST', '/v2/message', body=message)
	message = property(__get_message, __set_message)

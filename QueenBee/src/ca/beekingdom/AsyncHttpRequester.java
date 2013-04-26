package ca.beekingdom;

import java.util.concurrent.Callable;

import org.apache.http.HttpResponse;
import org.apache.http.client.HttpClient;
import org.apache.http.client.methods.HttpUriRequest;
import org.apache.http.util.EntityUtils;
import org.apache.log4j.Logger;

class AsyncHttpRequester implements Callable<Void> {
	private final Logger log = Logger.getLogger(getClass());

	private HttpClient httpClient;
	private HttpUriRequest request;

	public AsyncHttpRequester(HttpClient httpClient, HttpUriRequest request) {
		this.httpClient = httpClient;
		this.request = request;
	}

	@Override
	public Void call() throws Exception {
		try {
			HttpResponse response = httpClient.execute(request);
			int status = response.getStatusLine().getStatusCode();
			if(status != 200) {
				log.warn(request.getRequestLine() + " returned " + status);
			}
			EntityUtils.consume(response.getEntity());
		}
		catch(Exception ex) {
			log.error("HTTP request failed", ex);
			request.abort();
			throw ex;
		}
		return null;
	}
}
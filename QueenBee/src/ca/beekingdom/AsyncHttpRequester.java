package ca.beekingdom;

import java.util.concurrent.Callable;

import org.apache.http.HttpResponse;
import org.apache.http.client.HttpClient;
import org.apache.http.client.methods.HttpUriRequest;
import org.apache.http.util.EntityUtils;

class AsyncHttpRequester implements Callable<Void> {
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
			EntityUtils.consume(response.getEntity());
		}
		catch(Exception ex) {
			ex.printStackTrace(System.err);
			throw ex;
		}
		return null;
	}
}
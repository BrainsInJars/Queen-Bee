package ca.beekingdom;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;
import java.io.Reader;
import java.net.URI;
import java.net.URISyntaxException;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Observable;
import java.util.Observer;
import java.util.Properties;
import java.util.concurrent.Callable;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

import org.apache.commons.io.IOUtils;
import org.apache.http.Header;
import org.apache.http.client.HttpClient;
import org.apache.http.client.methods.HttpPut;
import org.apache.http.client.params.ClientPNames;
import org.apache.http.client.utils.URIBuilder;
import org.apache.http.conn.ClientConnectionManager;
import org.apache.http.conn.DnsResolver;
import org.apache.http.conn.scheme.SchemeRegistry;
import org.apache.http.entity.ContentType;
import org.apache.http.entity.StringEntity;
import org.apache.http.impl.client.DefaultHttpClient;
import org.apache.http.impl.conn.PoolingClientConnectionManager;
import org.apache.http.impl.conn.SchemeRegistryFactory;
import org.apache.http.impl.conn.SystemDefaultDnsResolver;
import org.apache.http.message.BasicHeader;
import org.apache.http.params.CoreProtocolPNames;
import org.apache.http.params.HttpParams;
import org.apache.http.params.SyncBasicHttpParams;
import org.apache.log4j.Level;
import org.apache.log4j.Logger;

import com.pi4j.io.gpio.GpioFactory;

public class QueenBee implements Observer {
	private static final Logger log = Logger.getLogger(QueenBee.class);

	private static final String HTTP_USER_AGENT = "http.user_agent";
	private static final String HTTP_FROM = "http.from";

	private static final String COSM_HOST = "cosm.host";
	private static final String COSM_API_KEY = "cosm.api_key";
	private static final String COSM_FEED_ID = "cosm.feed_id";
	
	private static final String COSM_UPDATE_INTERVAL = "cosm.update_interval";

	private static final String LOG_LEVEL = "log.level";

	private static final ContentType TEXT_CSV = ContentType.create("text/csv", "UTF8");

	private static SchemeRegistry schemeRegistry;
	private static DnsResolver dnsResolver;
	private static HttpParams httpParams;

	private static HttpClient httpClient;
	private static ClientConnectionManager connManager;

	private final ScheduledExecutorService executor;

	private URI cosmResource;

	public QueenBee(final ScheduledExecutorService executor, final Properties config) {
		this.executor = executor;

		URIBuilder uriBuilder = new URIBuilder();

		uriBuilder.setScheme("https");
		uriBuilder.setHost(config.getProperty(COSM_HOST));
		uriBuilder.setPath(String.format("/v2/feeds/%s", config.getProperty(COSM_FEED_ID)));

		try {
			cosmResource = uriBuilder.build();
		} catch(URISyntaxException ex) {
			ex.printStackTrace(System.err);
			System.exit(-1);
		}
	}

	public static void main(String[] args) {
		Properties userConfig = loadUserConfig("/etc/queenbee");

		log.info("Service starting");
		long cosmUpdateInterval = 10000;
		try {
			cosmUpdateInterval = Long.valueOf(userConfig.getProperty(COSM_UPDATE_INTERVAL));
		}
		catch(Exception ex) {
			log.warn("Unable to configure update interval", ex);
		}
		cosmUpdateInterval = Math.max(600, cosmUpdateInterval);
		log.debug(String.format("COSM Update Interval: %dms", cosmUpdateInterval));

		configureHttpClient(userConfig);
		log.info("HTTP client configured");

		IdleConnectionMonitor idleMonitor = new IdleConnectionMonitor(connManager);
		ScheduledExecutorService executor = Executors.newSingleThreadScheduledExecutor();
		executor.scheduleWithFixedDelay(idleMonitor, 60, 60, TimeUnit.SECONDS);

		log.info("Starting GPIO");
		QueenBee qb = new QueenBee(executor, userConfig);
		GpioMonitor gpioMonitor = new GpioMonitor(GpioFactory.getInstance());

		gpioMonitor.addObserver(qb);
		try {
			for(;;) {
				Thread.sleep(cosmUpdateInterval);
				gpioMonitor.observeState();
			}
		}
		catch(InterruptedException ex) {
			log.info("Received shutdown command");
		}

		try {
			if(!executor.awaitTermination(3, TimeUnit.SECONDS)) {
				executor.shutdownNow();
				log.warn("Forcing termination of pending tasks");
			}
			log.info("Service terminated");
		} catch(InterruptedException ex) {
			executor.shutdownNow();
			log.warn("Shutdown interrupted");
		}
	}

	private static Properties loadUserConfig(String src) {
		return loadUserConfig(new File(src));
	}
	private static Properties loadUserConfig(File src) {
		Reader reader;

		try {
			reader = new FileReader(src);
		}
		catch(FileNotFoundException ex) {
			return getDefaultConfig();
		}

		Properties userConfig = loadUserConfig(reader);
		IOUtils.closeQuietly(reader);

		return userConfig;
	}
	private static Properties loadUserConfig(Reader src) {
		Properties userConfig = new Properties(getDefaultConfig());

		try {
			userConfig.load(src);
		} catch(IOException e) {
			e.printStackTrace(System.err);
		}

		return userConfig;
	}
	private static Properties getDefaultConfig() {
		Properties defaultConfig = new Properties();

		defaultConfig.setProperty(COSM_HOST, "api.cosm.com");
		defaultConfig.setProperty(COSM_UPDATE_INTERVAL, "60000");

		defaultConfig.setProperty(LOG_LEVEL, "INFO");

		return defaultConfig;
	}

	private static void configureHttpClient(Properties config) {
		schemeRegistry = SchemeRegistryFactory.createSystemDefault();
		httpParams = new SyncBasicHttpParams();
		dnsResolver = new SystemDefaultDnsResolver();

		connManager = new PoolingClientConnectionManager(schemeRegistry, dnsResolver);

		if(config.containsKey(HTTP_USER_AGENT)) {
			httpParams.setParameter(CoreProtocolPNames.USER_AGENT, config.getProperty(HTTP_USER_AGENT));
		}

		Collection<Header> headers = new ArrayList<Header>();
		if(config.containsKey(HTTP_FROM)) {
			headers.add(new BasicHeader("From", config.getProperty(HTTP_FROM)));
		}
		headers.add(new BasicHeader("X-ApiKey", config.getProperty(COSM_API_KEY)));
		httpParams.setParameter(ClientPNames.DEFAULT_HEADERS, headers);

		httpClient = new DefaultHttpClient(connManager, httpParams);
	}
	
	@Override
	public void update(Observable o, Object arg) {
		Integer flameLevel = (Integer)arg;

		log.info(flameLevel);

		HttpPut request = new HttpPut(cosmResource);
		StringBuilder builder = new StringBuilder();
		builder.append(String.format("\"flame_level\",\"%d\"\n", flameLevel));

		request.setEntity(new StringEntity(builder.toString(), TEXT_CSV));
		Callable<Void> update = new AsyncHttpRequester(httpClient, request);
		executor.submit(update);
	}
}

package ca.beekingdom;

import java.util.concurrent.TimeUnit;

import org.apache.http.conn.ClientConnectionManager;


public class IdleConnectionMonitor implements Runnable {
	private final ClientConnectionManager connManager;

	private final long idleTime;
	private final TimeUnit timeUnit;

	public IdleConnectionMonitor(ClientConnectionManager connManager) {
		this(connManager, 60, TimeUnit.SECONDS);
	}
	public IdleConnectionMonitor(ClientConnectionManager connManager, long idleTime, TimeUnit timeUnit) {
		this.connManager = connManager;
		
		this.idleTime = idleTime;
		this.timeUnit = timeUnit;
	}

	@Override
	public void run() {
		synchronized(this) {
			connManager.closeExpiredConnections();
			connManager.closeIdleConnections(idleTime, timeUnit);
		}
	}
}

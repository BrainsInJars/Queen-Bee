package ca.beekingdom;

import java.util.Observable;

import com.pi4j.io.gpio.GpioController;
import com.pi4j.io.gpio.GpioPinDigitalInput;
import com.pi4j.io.gpio.PinPullResistance;
import com.pi4j.io.gpio.RaspiPin;
import com.pi4j.io.gpio.event.GpioPinDigitalStateChangeEvent;
import com.pi4j.io.gpio.event.GpioPinListenerDigital;

public class GpioMonitor extends Observable implements GpioPinListenerDigital {
	private final GpioPinDigitalInput pinOk;
	private final GpioPinDigitalInput pinLo;
	private final GpioPinDigitalInput pinHi;

	public GpioMonitor(final GpioController controller) {
		pinOk = controller.provisionDigitalInputPin(RaspiPin.GPIO_00, PinPullResistance.OFF);
		pinLo = controller.provisionDigitalInputPin(RaspiPin.GPIO_01, PinPullResistance.OFF);
		pinHi = controller.provisionDigitalInputPin(RaspiPin.GPIO_02, PinPullResistance.OFF);

		pinOk.addListener(this);
		pinLo.addListener(this);
		pinHi.addListener(this);
	}

	@Override
	public void handleGpioPinDigitalStateChangeEvent(GpioPinDigitalStateChangeEvent evt) {
		observeState();
	}

	public void observeState() {
		int pinState = 0;
		pinState |= pinOk.isLow() ? 0x1 : 0x0;
		pinState |= pinLo.isLow() ? 0x2 : 0x0;
		pinState |= pinHi.isLow() ? 0x4 : 0x0;

		if(((1 << pinState) & 0x16) == 0) {
			return;
		}

		int flameLevel = 0;
		if(pinState == 0x2) {
			flameLevel = -1;
		} else if(pinState == 0x4) {
			flameLevel = 1;
		}

		setChanged();
		notifyObservers(Integer.valueOf(flameLevel));
	}
}

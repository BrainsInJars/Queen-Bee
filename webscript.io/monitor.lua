local twilio = require 'twilio'

local timeout = json.parse(storage.timeout or "180");
local system_failure = json.parse(storage.system_failure or "false");

local last_beat = json.stringify(os.time());
last_beat = json.parse(storage.heartbeat or last_beat);

function sms(msg)
	callees = json.parse(storage.callees or '[]')
	for n, number in ipairs(callees) do
		twilio.sms(storage.account_sid, storage.auth_token, storage.from, number, msg)
	end
end

delta = os.difftime(os.time(), last_beat);
if delta < timeout then
	if system_failure then
		-- System is back up
		elapsed = os.time() - system_failure;
		storage.system_failure = json.stringify(False);
		sms('The monitoring system is back up ('..elapsed..'s)')
	else
		log('The monitoring system is OK');
	end
else
	if system_failure then
		log('The monitoring system is down');
	else
		-- System just failed
		storage.system_failure = json.stringify(last_beat);
		sms('The monitoring system has failed');
	end
end

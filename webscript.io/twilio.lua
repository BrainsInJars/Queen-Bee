local twilio = require 'twilio'

if not twilio.verify(request, storage.auth_token) then
	return 403
end

local conference = tonumber(request.query.conference or '0');
local twiml = '<?xml version="1.0" encoding="UTF-8"?><Response>'

if request.form.MessageSid then
	local command = string.lower(request.form.Body)
	local response = 'Unknown command "'..command..'" try "commands"'
	local t = {
		['cats'] = '<body>Enjoy this picture of a cat!</body><Media>http://thecatapi.com/api/images/get</Media>',
		['status'] = '<Body>'..(storage.status_message or '')..'</Body>',
		['commands'] = [[<Body>Available Commands:
"status" - current system status
"commands" - display this list of commands
"cats" - a picture of a cat</Body>]]
	}
	if t[command] ~= nil then
		response = t[command]
	end

	twiml = twiml .. '<Message to="'..request.form.From..'" from="'..request.form.To..'">'
	twiml = twiml .. response
	twiml = twiml .. '</Message>'
elseif request.form.CallSid then
	twiml = twiml..'<Say voice="woman">'
	twiml = twiml..storage.status_message or ''

	if conference ~= 0 then
		twiml = twiml..' Connecting with other participants.'
	end

	twiml = twiml..'</Say>'

	if conference ~= 0 then
		twiml = twiml..'<Dial><Conference>queenbee</Conference></Dial>'
	end
end

twiml = twiml..'</Response>'

return twiml, {['Content-Type']='application/xml'}

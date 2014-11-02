local auth = require('BrainsInJars/wsauth/signed.lua');
if not auth.authenticate(request) then
	return 403;
end

storage.heartbeat = os.time()

return 200

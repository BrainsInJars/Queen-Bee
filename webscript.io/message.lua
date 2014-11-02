local auth = require('BrainsInJars/wsauth/signed.lua');
if not auth.authenticate(request) then
	return 403;
end

if request.method == 'GET' then
	return 200, storage.status_message or '';
elseif request.method == 'POST' then
	storage.status_message = json.parse(request.body);
end

return 200

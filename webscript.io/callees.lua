local auth = require('BrainsInJars/wsauth/signed');

if not auth.authenticate(request) then
	return 403;
end

if request.method == 'GET' then
	return 200, storage.callees;
elseif request.method == 'POST' then
	local body = json.parse(request.body)

	local dupes = {}
	local callees = {}

	for n, number in ipairs(body) do
		if string.match(number, '^\+1%d+$') and string.len(number) == 12 then
			if dupes[number] then
				log('"'..number..'" is a duplicate');
			else
				dupes[number] = true;
				table.insert(callees, number)
			end
		else
			log('"'..number..'" Does not appear to be a valid phone number');
		end
	end

	storage.callees = json.stringify(callees);
end

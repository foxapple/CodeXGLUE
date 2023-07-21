from urllib.request import Request, urlopen
import json

req = Request('https://msesandbox.cisco.com/api/contextaware/v1/maps/info/DevNetCampus/DevNetBuilding')
req.add_header('Authorization', 'Basic bGVhcm5pbmc6bGVhcm5pbmc==')
req.add_header('Accept', 'application/json')
response = urlopen(req)
response_string = response.read().decode("utf-8")

json_object = json.loads(response_string)

print(json_object["Building"])

#floors = json_object["Building"]["Floor"]
#for floor in floors:
#	print("Floor Number: " + str(floor["floorNumber"]))
#	aps = floor["AccessPoint"]
#	for ap in aps:
#		print(" " + ap["name"] + "/" + ap["ipAddress"] + "/")

response.close()
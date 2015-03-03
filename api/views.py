from django.http import HttpResponse
from django.core import serializers

from django.views.decorators.csrf import csrf_exempt

import json
from django.forms.models import model_to_dict

from django.core.exceptions import ObjectDoesNotExist

from clients.models import Hotspot, Client
from unifi_control.models import UnifiController

@csrf_exempt
def hotspot(request, id):
	hotspot = Hotspot.objects.filter(external_id = id).first()
		
	if not hotspot:
		data = { 'error': 'No hotspot found' }
		
		return HttpResponse(json.dumps(data), content_type='application/json')
	
	client = hotspot.client
	portal = client.portal
	
	controller = client.unifi_controller.controller(client.unifi_site)
		
	if request.method == 'POST':
		try:
			data = json.loads(request.body)
		except:
			data = None
			
		if type(data) is dict:
			# Update hotspot data
			
			if 'access_methods' in data.keys() and 'facebook' in data['access_methods']:
				facebook = data['access_methods']['facebook']
				
				if 'enabled' in facebook.keys():
					if not facebook['enabled']:
						portal.facebook_page_id = None
					
				if 'page_id' in facebook.keys() and facebook['page_id']:
					portal.facebook_page_id = facebook['page_id']
					
			if 'network_password' in data.keys():
				network_password = data['network_password']
				
				if 'enabled' in network_password.keys():
					if not network_password['enabled']:
						portal.wpa_password = None
					
				if 'wpa_password' in network_password.keys() and network_password['wpa_password']:
				
					if len(network_password['wpa_password']) >= 8:
						portal.wpa_password = network_password['wpa_password']
						
						controller.set_wpa_password(portal.wpa_password)
					else:
						data = { 'error': 'The WPA password should have a length of at least 8 characters.' }
						
						return HttpResponse(json.dumps(data), content_type='application/json')
					
			portal.save()
	
	# Output
	data = model_to_dict(hotspot)
	
	# Remove internal ID
	data.pop('external_id', None)
	data['id'] = hotspot.external_id
	
	# Get status
	try:
		ap = [ap for ap in controller.get_aps() if ap['mac'] == hotspot.mac_address][0]
		
		data['online'] = 'state' in ap.keys() and ap['state']
	except IndexError:
		pass
	
	'''
	# Embed client
	client = model_to_dict(client)
	fields = ['company_name', 'contact_name', 'email', 'street', 'number', 'postal', 'city', 'country']
	
	data['client'] = { key: client[key] for key in fields }
	'''
	
	del data['client']
	
	# Access methods
	data['access_methods'] = { "facebook": { "enabled": portal.facebook_enabled(), "page_id": portal.facebook_page_id } }
	
	# Network password
	data['network_password'] = { "enabled": portal.network_password_enabled(), "wpa_password": portal.wpa_password }
	
	return HttpResponse(json.dumps(data), content_type='application/json')
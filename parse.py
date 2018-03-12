import os
import datetime
import shutil
import xmltodict
import json
import hashlib
import sys
import pprint

OUTPUT_PATH = './output/idp_hint/'
ADMIN_OUTPUT_PATH = './output/admin/'
ENTITY_ID_OUTPUT = 'entityids.json'
DISPLAY_NAME_OUTPUT = 'display_names.json'
DISPLAY_NAME_COUNTRY_OUTPUT = 'display_names_country.json'
REGISTRATION_AUTHORITY_OUTPUT = 'registration_authorities.json'
BLACKLIST_OUTPUT = 'blacklist.json'
WHITELIST_OUTPUT = 'whitelist.json'
WRITE_FILES = True

entity_id_idp_map = {}
display_name_idp_map = {}
display_name_country_idp_map = {}
registrationAuthorities_map = {}
idp_blacklist = {}
idp_whitelist_website = {}

# Load whitelisted IdPs and blacklisted keywords from file
blacklisted_keywords = [line.rstrip('\n') for line in open('config/blacklisted_keywords.txt')]
idp_whitelisted_entities = [line.rstrip('\n') for line in open('config/idp_whitelisted_entities.txt')]

#idp_whitelist_names = {'Bishop Grosseteste University', ' KGV College - Latest'}

# Some counters for reporting
num_processed = 0
num_blacklisted = 0

# TODO: write soemthign to update xml from edugain.
# wget http://md.edugain.org -O edugain.xml

with open('./input/edugain.xml') as fd:
    entities = xmltodict.parse(fd.read())

numEntities =len(entities['md:EntitiesDescriptor']['md:EntityDescriptor'])

for entnr in range(0, numEntities):
  entity = entities['md:EntitiesDescriptor']['md:EntityDescriptor'][entnr]

  if 'md:IDPSSODescriptor' in entity:
    # Found an IdP  
    entity_id = entity['@entityID']
    entity_id_hash = hashlib.sha1(entity_id.encode('utf-8')).hexdigest()

    entity_id_idp_map[entity_id_hash] = entity_id

    registrationAuthority = entity['md:Extensions']['mdrpi:RegistrationInfo']['@registrationAuthority']
    if registrationAuthority == "https://incommon.org":
     registrationAuthorityCountry = "us"
    elif registrationAuthority == "http://kafe.kreonet.net":
     registrationAuthorityCountry = "kr"
    elif registrationAuthority ==  "http://www.csc.fi/haka":
     registrationAuthorityCountry = "fi"
    else:
     registrationAuthorityCountry = registrationAuthority.split(".")[-1].replace("/","")   
     registrationAuthorities_map[registrationAuthorityCountry] = registrationAuthority

    entDescIdPExt = entity['md:IDPSSODescriptor']['md:Extensions']
    display_name_map = {}
	
    # set the display_name to be the entityID (should always work)
    display_name_map['en'] = entity_id
    try:
      # Try to past mdui displayname - may throw KeyError of there is no mdui
      # Try to parse single mdui displayname - may throw TypeError of there is multiple
      display_name_map[entDescIdPExt['mdui:UIInfo']['mdui:DisplayName']['@xml:lang']] = entDescIdPExt['mdui:UIInfo']['mdui:DisplayName']['#text']
    except TypeError:
      display_name_map[entDescIdPExt['mdui:UIInfo']['mdui:DisplayName'][0]['@xml:lang']] = entDescIdPExt['mdui:UIInfo']['mdui:DisplayName'][0]['#text']
      display_name_map[entDescIdPExt['mdui:UIInfo']['mdui:DisplayName'][1]['@xml:lang']] = entDescIdPExt['mdui:UIInfo']['mdui:DisplayName'][1]['#text']
    except KeyError:
      # Just use previously set entityid
      pass

    # test if the IdP does not have names we doe not allow from the blacklist
    if any(x in display_name_map['en'] for x in blacklisted_keywords):
      # But do check if they are not whitelisted
      if not any(x in display_name_map['en'] for x in idp_whitelisted_entities):
        idp_blacklist[entity_id] = display_name_map['en']
        num_blacklisted=num_blacklisted+1
    else:
      # IF we have a new country, make a map for it
      if registrationAuthorityCountry not in display_name_country_idp_map:
        display_name_country_idp_map[registrationAuthorityCountry] = {}
        idp_whitelist_website[registrationAuthorityCountry] = {}
      # set name to the per country map
      display_name_country_idp_map[registrationAuthorityCountry][entity_id_hash] = display_name_map
      # set name to the per country map whitelist
      idp_whitelist_website[registrationAuthorityCountry][entity_id] = display_name_map
      
      #set the full list
      display_name_idp_map[entity_id_hash] = display_name_map['en']
      num_processed = num_processed + 1

#print "Numer of IdPs processed: ", num_processed
#print "Numer of IdPs blacklisted: ", num_blacklisted

# prepend whitelist and registrationAuthorities so these can be used as JSONP
idp_whitelist_website_outfile = 'processIdPs(\n' + json.dumps(idp_whitelist_website, sort_keys=True, indent=4) + '\n);'
registrationAuthorities_map_outfile = 'processFederations(\n' + json.dumps(registrationAuthorities_map, sort_keys=True, indent=4) + '\n);'

if WRITE_FILES:
  # Now dump the dict to a json format
  with open(ADMIN_OUTPUT_PATH + ENTITY_ID_OUTPUT, 'w') as outfile:
      json.dump(entity_id_idp_map, outfile, sort_keys=True, indent=4)
  with open(OUTPUT_PATH + DISPLAY_NAME_OUTPUT, 'w') as outfile:
      json.dump(display_name_idp_map, outfile, sort_keys=True, indent=4)
  with open(OUTPUT_PATH + DISPLAY_NAME_COUNTRY_OUTPUT, 'w') as outfile:
      json.dump(display_name_country_idp_map, outfile, sort_keys=True, indent=4)
  with open(ADMIN_OUTPUT_PATH + BLACKLIST_OUTPUT, 'w') as outfile:
      json.dump(idp_blacklist, outfile, sort_keys=True, indent=4)
  with open(ADMIN_OUTPUT_PATH + WHITELIST_OUTPUT, 'w') as outfile:
      #print(idp_whitelist_website_outfile, file=outfile)
      outfile.write(idp_whitelist_website_outfile)
  with open(ADMIN_OUTPUT_PATH + REGISTRATION_AUTHORITY_OUTPUT, 'w') as outfile:
	  #print(registrationAuthorities_map_outfile, file=outfile)
	  outfile.write(registrationAuthorities_map_outfile)
  # Use a per registrar list to generate per country data
  for key, value in registrationAuthorities_map.items():
    # print key
    with open(OUTPUT_PATH + key+".json", 'w') as outfile:
      json.dump(display_name_country_idp_map[key], outfile, sort_keys=True, indent=4)

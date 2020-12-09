import os
import datetime
import shutil
import xmltodict
import json
import hashlib
import urllib
import sys
import wget
import time
#import pprint
#import os.path as path

HINTING_ROOTPATH=os.environ['HINTING_ROOTPATH']
CONFIG_PATH=os.environ['CONFIG_PATH']
RA_INPUT_PATH = os.environ['FEEDS_PATH']
OUTPUT_PATH = os.environ['IDP_HINT_PATH']
ADMIN_OUTPUT_PATH = os.environ['ADMIN_DATA_PATH']
ADMIN_HASHES_PATH = os.environ['ADMIN_HASHES_PATH']
ADMIN_INPUT_PATH = os.environ['ADMIN_DATA_REPO_PATH']

ENTITY_ID_OUTPUT = '/entityids.json'
DISPLAY_NAME_OUTPUT = '/display_names.json'
ENTITY_ID_COUNTRY_OUTPUT = '/entityids_country.json'
ENTITY_ID_RA_OUTPUT = '/entityids_ra.json'
DISPLAY_NAME_COUNTRY_OUTPUT = '/display_names_country.json'
REGISTRATION_AUTHORITY_OUTPUT = '/registration_authorities.json'
BLACKLIST_OUTPUT = '/blacklist.json'
WHITELIST_OUTPUT = '/whitelist.json'
EDUGAIN_RA_URI = 'https://www.edugain.org'
WRITE_FILES = True

# These are te dicts we maintain to create the lists to write out.
entity_id_idp_map = {}
entity_id_ra_map = {}
display_name_idp_map = {}
entity_id_country_map = {}
display_name_country_idp_map = {}
registrationAuthorities_map = {}
country_idp_map = {}
entity_id_ra_map = {}
idp_blacklist = {}
idp_whitelist_website = {}

# Load whitelisted IdPs and blacklisted keywords from file
blacklisted_keywords = [line.rstrip('\n') for line in open(CONFIG_PATH + '/blacklisted_keywords.txt')]
idp_whitelisted_entities = [line.rstrip('\n') for line in open(CONFIG_PATH + '/idp_whitelisted_entities.txt')]

# Some counters for reporting
num_processed = 0
num_blacklisted = 0
num_idps = 0

entities = {}

def is_file_older_than_x_days(file, days=1):
    file_time = os.path.getmtime(file)
    # Check against 24 hours
    if (time.time() - file_time) / 3600 > 24*days:
        return True
    else:
        return False

def fetchXML(url, file_path):
  try:
    urllib.request.urlretrieve(url, file_path)
    return True
  except:
    return False

def parseMetadataXML(schema_prefix, file_path):
    try:
      with open(file_path) as fd:
          ent = xmltodict.parse(fd.read())

      print("INFO: Entities found : ", len(ent[schema_prefix + 'EntitiesDescriptor'][schema_prefix + 'EntityDescriptor']))
      return ent

    except:
      print("ERROR: Could not parse " +file_path)
      return {}


def readMetadata(md_url, schema_prefix, raname, file_path):
  if md_url:
    if os.path.isfile(file_path) and not (is_file_older_than_x_days(file_path, 1)):
      print("INFO: " + raname + " metadata still up to date, skipping download")
    else:
      print("INFO: " + raname + " metadata out of date, downloading from " + md_url)

      if (fetchXML(md_url, file_path)):
        print("INFO: Downloaded metadata URL: " + md_url + " to file location: " + file_path)
      else:
        print("ERROR: Could not download metadata URL: " + md_url)
        return {}

    return parseMetadataXML(schema_prefix, file_path)

  else:
    print("ERROR: No metadata URL provided")
    return {}

def loadRAconfig():
  with open(CONFIG_PATH + '/RAs.json') as ras_file:
    return json.load(ras_file)

def loadIdPs():
  try:
    with open(ADMIN_INPUT_PATH + ENTITY_ID_OUTPUT) as idps_file:
      return json.load(idps_file)
  except:
    return {}

def isEduGAIN(ra_uri, edugain_uri):
  if ra_uri == edugain_uri:
    return True
  else:
    return False

def processEntities(ra, schema_prefix):
  # we parse all eduGAIN metadata
  # if we find and RA we have special rules for we will apply these
  # if we find a RA with own metadata we skipp it

  print("Current RA:", ra)

  # parse RA specfific metadata
  num_idps = 0
  num_processed = 0
  num_blacklisted = 0

  # Count how many antities we have in the current xml object
  # if there is no metadata this fails with a keyError
  try:
    numEntities = len(entities[ra][schema_prefix + 'EntitiesDescriptor'][schema_prefix + 'EntityDescriptor'])
    print("INFO: Entities that need to be processed in " +ra + ": ", numEntities)
  except KeyError:
    numEntities = 0
    print("INFO: No entities to process for " +ra +", using eduGAIN metadata")

  # Set RA to be RA provided as a default
  #registrationAuthority = ra

  for entnr in range(0, numEntities):
    entity = entities[ra][schema_prefix + 'EntitiesDescriptor'][schema_prefix + 'EntityDescriptor'][entnr]

    if (schema_prefix + 'IDPSSODescriptor') in entity:
      # Found an IdP
      num_idps = num_idps + 1
      entity_id = entity['@entityID']

      #print("Entity ", entity_id)

      # Calucluate the HASH for IdP hinting as aSHA1 over the entityID
      entity_id_hash = hashlib.sha1(entity_id.encode('utf-8')).hexdigest()

      entity_id_idp_map[entity_id_hash] = entity_id

      # fetch RA from eduGAIN metadata
      if ra == EDUGAIN_RA_URI:
        registrationAuthority = entity[schema_prefix + 'Extensions']['mdrpi:RegistrationInfo']['@registrationAuthority']
      else:
        registrationAuthority = ra

      entity_id_ra_map[entity_id_hash] = registrationAuthority

      # test if this RA has special behaviour
      #if registrationAuthority in RAs:
      #    print("Found RA from config: ", registrationAuthority)

      # By default we fetch country from RA URI
      # may need correction lateron, but this saves us if statements
      registrationAuthorityCountry = registrationAuthority.split(".")[-1].replace("/","")

      try:
        if RAs[registrationAuthority]["country_code"]:
          registrationAuthorityCountry = RAs[registrationAuthority]["country_code"]
      except KeyError:
        # just use the ra country from the uri
        pass

      # TODO: what if we have multiple RAs per country?
      registrationAuthorities_map[registrationAuthorityCountry] = registrationAuthority

      # Start working on parsing the displayname
      display_name_map = {}

      # set the display_name to be the entityID (should always work)
      display_name_map['en'] = entity_id

      # Try to find element that shoudl hold the MDUI info
      try:
        entDescIdPExt = entity[schema_prefix + 'IDPSSODescriptor'][schema_prefix + 'Extensions']

      except KeyError:
        pass

      try:
        # Try to get mdui displayname - may throw KeyError of there is no mdui
        # Try to parse single mdui displayname - may throw TypeError of there is multiple
        display_name_map[entDescIdPExt['mdui:UIInfo']['mdui:DisplayName']['@xml:lang']] = entDescIdPExt['mdui:UIInfo']['mdui:DisplayName']['#text']
      except TypeError:
        display_name_map[entDescIdPExt['mdui:UIInfo']['mdui:DisplayName'][0]['@xml:lang']] = entDescIdPExt['mdui:UIInfo']['mdui:DisplayName'][0]['#text']
        display_name_map[entDescIdPExt['mdui:UIInfo']['mdui:DisplayName'][1]['@xml:lang']] = entDescIdPExt['mdui:UIInfo']['mdui:DisplayName'][1]['#text']
      except KeyError:
        # Just use previously set entityid
        print("WARN: No mdui information for entityID: ",  display_name_map['en'])
        pass

      country_idp_map.setdefault(registrationAuthorityCountry, {})
      country_idp_map[registrationAuthorityCountry][entity_id] = f"{display_name_map['en']}, {entity_id_hash}"

      entity_blacklisted = False

      # test if the IdP does not have names we do not allow from the blacklist
      if any(x in display_name_map['en'] for x in blacklisted_keywords):
        entity_blacklisted = True
        # But do check if they are not whitelisted
        if any(x in display_name_map['en'] for x in idp_whitelisted_entities):
          entity_blacklisted = False

      if entity_blacklisted:
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
        entity_id_country_map[entity_id_hash] = registrationAuthorityCountry
        num_processed = num_processed + 1

  #print("Numer of IdPs found: ", num_idps)
  #print("Numer of IdPs processed: ", num_processed)
  #print("Numer of IdPs blacklisted: ", num_blacklisted)

def outputFiles():
   # Now dump the dict to a json format
   with open(ADMIN_OUTPUT_PATH + ENTITY_ID_OUTPUT, 'w') as outfile:
      json.dump(entity_id_idp_map, outfile, sort_keys=True, indent=4)
   with open(ADMIN_OUTPUT_PATH + ENTITY_ID_COUNTRY_OUTPUT, 'w') as outfile:
      json.dump(entity_id_country_map, outfile, sort_keys=True, indent=4)
   with open(ADMIN_OUTPUT_PATH + BLACKLIST_OUTPUT, 'w') as outfile:
      json.dump(idp_blacklist, outfile, sort_keys=True, indent=4)
   with open(ADMIN_OUTPUT_PATH + ENTITY_ID_RA_OUTPUT, 'w') as outfile:
      json.dump(entity_id_ra_map, outfile, sort_keys=True, indent=4)
   with open(ADMIN_OUTPUT_PATH + WHITELIST_OUTPUT, 'w') as outfile:
      #print(idp_whitelist_website_outfile, file=outfile)
      outfile.write(idp_whitelist_website_outfile)
   with open(ADMIN_OUTPUT_PATH + REGISTRATION_AUTHORITY_OUTPUT, 'w') as outfile:
      #print(registrationAuthorities_map_outfile, file=outfile)
      outfile.write(registrationAuthorities_map_outfile)

   with open(OUTPUT_PATH + DISPLAY_NAME_OUTPUT, 'w') as outfile:
      json.dump(display_name_idp_map, outfile, sort_keys=True, indent=4)
   with open(OUTPUT_PATH + DISPLAY_NAME_COUNTRY_OUTPUT, 'w') as outfile:
      json.dump(display_name_country_idp_map, outfile, sort_keys=True, indent=4)
   # Use a per registrar list to generate per country data
   for key, value in registrationAuthorities_map.items():
     # print key
     with open(OUTPUT_PATH + '/' + key + ".json", 'w') as outfile:
       json.dump(display_name_country_idp_map[key], outfile, sort_keys=True, indent=4)
     with open(ADMIN_HASHES_PATH + '/' + key + ".json", 'w') as outfile:
       #json.dump(country_idp_map[key], outfile, sort_keys=True, indent=4)
       #Sort on displayname, keep entity_id as key value
       json.dump({k:v for k,v in sorted(country_idp_map[key].items(), key=lambda item: item[1])}, outfile, indent=4)

def setRAdata(raconf):
  # Read RA config and loads RA metadata
  RAs={}

  for ra in raconf.keys():
     RAs[ra] = {}

     schema_prefix = raconf[ra]["schema_prefix"]
     md_url = raconf[ra]["md_url"]
     ra_name = raconf[ra]["name"]
     file_path = RA_INPUT_PATH + '/' + ra_name +'.xml'

     entities[ra] = readMetadata(md_url, schema_prefix, ra_name, file_path)
     RAs[ra]["schema_prefix"] = schema_prefix
     RAs[ra]["md_url"] = md_url
     RAs[ra]["ra_name"] = ra_name
     RAs[ra]["country_code"] = raconf[ra]["country_code"]
     RAs[ra]["file_path"] = file_path
     RAs[ra]["hasOwnMetadata"] = bool(len(entities[ra]))
     RAs[ra]["isEduGAIN"] = isEduGAIN(ra, EDUGAIN_RA_URI )

  return RAs

# Main code starts here

# by default we process all RAs from eduGAIN, however some need special treatment, as defined by the RAs config file.

# The config file provides the following capabiliteis (using eduGAIN as an example):
#
#	"https://www.edugain.org": {                  -> Identifier of the RA - cannot be empty
#		"name": "eduGAIN",                        -> Displayname of the RA  - cannot be empty
#		"country_code": "",                       -> 2 letter country code to use for this RA. By default the country code is derived from the RA FQDN. use this value to overrule for this RA - ignored if empty
#		"md_url": "http://mds.edugain.org",       -> Metadata URL to use for this RA. If not empty, this metadata will prevail over any eduGAIN metadata. If left empty, edugain metadata will be used for this RA - ignored if empty
#       "schema_prefix" : "md:"                   -> Matdata may come with a specific prefix. Use this to postfix the metadata prefix used for the configured md_url.
#	},
#
raConf = loadRAconfig()
RAs = setRAdata(raConf)
entity_id_idp_old = loadIdPs()

# Now deal with the others
for ra in RAs.keys():
    print ("Working on ", ra)
    processEntities(ra, RAs[ra]["schema_prefix"])

# prepend whitelist and registrationAuthorities so these can be used as JSONP
idp_whitelist_website_outfile = 'processIdPs(\n' + json.dumps(idp_whitelist_website, sort_keys=True, indent=4) + '\n);'
registrationAuthorities_map_outfile = 'processFederations(\n' + json.dumps(registrationAuthorities_map, sort_keys=True, indent=4) + '\n);'

if WRITE_FILES:
   outputFiles()

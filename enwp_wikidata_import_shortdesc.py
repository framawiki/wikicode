# !/usr/bin/python
# -*- coding: utf-8  -*-
# Synchronise enwp short description and wikidata en descriptions
# Mike Peel     03-Aug-2020     v1 - start
# Mike Peel     12-Sep-2020     v2 - reconfigure just for empty Wikidata descriptions.

import pywikibot
from pywikibot import pagegenerators
from pywikibot.data import api

def get_pageinfo(site, itemtitle):
	 params = { 'action' :'query', 
				'format' : 'json',
				'prop' : 'pageprops',
				'titles': itemtitle}
	 request = api.Request(site=site, parameters=params)
	 return request.submit()

maxnum = 10000
nummodified = 0
debug = True
trip = True
# replace_existing = False
maxwords = 10

targetcat = 'Category:Short description with empty Wikidata description'
lower_exceptions = ['English', 'British', 'Spanish', 'French', 'France', 'Spain']

wikidata_site = pywikibot.Site("wikidata", "wikidata")
repo = wikidata_site.data_repository()  # this is a DataSite object
commons = pywikibot.Site('commons', 'commons')
wikipedia = pywikibot.Site('en', 'wikipedia')


cat = pywikibot.Category(wikipedia, targetcat)
pages = pagegenerators.CategorizedPageGenerator(cat, recurse=False);
for page in pages:
	enwiki_description = ''
	wikidata_description = ''

	if not trip:
		if "Varanasi" in page.title():
			trip = True
		else:
			print(page.title())
			continue
	try:
		wd_item = pywikibot.ItemPage.fromPage(page)
		item_dict = wd_item.get()
		qid = wd_item.title()
	except:
		print('Huh - no page found')
		continue

	print("\n" + qid)
	print('https://en.wikipedia.org/wiki/'+page.title().replace(' ','_'))

	# Get the short description from enwp
	test = get_pageinfo(wikipedia,page)
	for item in test['query']['pages']:
		enwiki_description = test['query']['pages'][item]['pageprops']['wikibase-shortdesc']
	if len(enwiki_description) > 0:
		if enwiki_description.split()[0] not in lower_exceptions:
			enwiki_description = enwiki_description[0].lower() + enwiki_description[1:]
		if enwiki_description[-1] == '.':
			enwiki_description = enwiki_description[0:-1]
	else:
		continue

	# Check the length of the short description
	print(enwiki_description)
	if len(enwiki_description.split()) > maxwords:
		print('enwiki description is too long, skipping')
		continue

	# Get the description from Wikidata
	try:
		wikidata_description = item_dict['descriptions']['en']
	except:
		null = 0

	# Save it to Wikidata
	if wikidata_description == '':
		# We have no en description on Wikidata, so we can add the enwp one
		print(enwiki_description)
		if debug:
			test = input('No description, import it?')
		else:
			test = 'y'
		mydescriptions = {u'en': enwiki_description}
		if test == 'y':
			wd_item.editDescriptions(mydescriptions, summary=u'Importing short description from the English Wikipedia')
			nummodified += 1
	# elif wikidata_description.lower() != enwiki_description.lower() and replace_existing:
	# 	# The Wikidata description doesn't match enwp, update it using enwp
	# 	print('enwp: ' + enwiki_description)
	# 	print('wikidata: ' + wikidata_description)
	# 	if debug:
	# 		test = input('Change description?')
	# 	else:
	# 		test = 'y'
	# 	mydescriptions = {u'en': enwiki_description}
	# 	if test == 'y':
	# 		wd_item.editDescriptions(mydescriptions, summary=u'Matching short description from the English Wikipedia')
	# 		nummodified += 1

	if nummodified > maxnum:
		break

print('Done! Edited ' + str(nummodified) + ' entries')
		
# EOF
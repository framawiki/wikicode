#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (C) 2017-2019 emijrp <emijrp@gmail.com>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re
import sys
import urllib

import pywikibot
from pywikibot import pagegenerators

import json
import os
import re
import sys
import _thread
import time
import unicodedata
import urllib
import urllib.request
import urllib.parse
import dateparser

def removeAccents(s):
   return ''.join(c for c in unicodedata.normalize('NFD', s)
				  if unicodedata.category(c) != 'Mn')

def getURL(url='', retry=True, timeout=30):
	raw = ''
	req = urllib.request.Request(url, headers={ 'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:55.0) Gecko/20100101 Firefox/55.0' })
	try:
		raw = urllib.request.urlopen(req, timeout=timeout).read().strip().decode('utf-8')
	except:
		sleep = 10 # seconds
		maxsleep = 900
		while retry and sleep <= maxsleep:
			print('Error while retrieving: %s' % (url))
			print('Retry in %s seconds...' % (sleep))
			time.sleep(sleep)
			try:
				raw = urllib.request.urlopen(req, timeout=timeout).read().strip().decode('utf-8')
			except:
				pass
			sleep = sleep * 2
	return raw

def isScriptAliveCore(pidfilename=''):
	while 1:
		with open(pidfilename, 'w') as f:
			f.write('alive')
		time.sleep(10)

def isScriptAlive(filename=''):
	alivefilename = '%s.alive' % (filename)
	if os.path.exists(alivefilename):
		print('Script is working, we wont launch another copy. Exiting...')
		os.remove(alivefilename)
		sys.exit()
	else:
		print('Alive file not found. We continue this instance')
		try:
		   _thread.start_new_thread(isScriptAliveCore, (alivefilename,) )
		except:
		   print("Error: unable to start thread")

def getUserEditCount(user='', site=''):
	if user and site:
		editcounturl = 'https://%s/w/api.php?action=query&list=users&ususers=%s&usprop=editcount&format=json' % (site, urllib.parse.quote(user))
		raw = getURL(editcounturl)
		json1 = json.loads(raw)
		if 'query' in json1 and 'users' in json1['query'] and 'editcount' in json1['query']['users'][0]:
			return json1['query']['users'][0]['editcount']
	return 0

def loadSPARQL(sparql=''):
	json1 = ''
	if sparql:
		try:
			json1 = json.loads(sparql)
			return json1
		except:
			print('Error downloading SPARQL? Malformatted JSON? Skiping\n')
			return 
	else:
		print('Server return empty file')
		return 
	return

def getAllCountries():
	url = 'https://query.wikidata.org/bigdata/namespace/wdq/sparql?query=SELECT%20%3FitemLabel%20%3Fitem%0AWHERE%20%7B%0A%09%3Fitem%20wdt%3AP31%20wd%3AQ6256.%0A%20%20%20%20SERVICE%20wikibase%3Alabel%20%7B%20bd%3AserviceParam%20wikibase%3Alanguage%20%22en%22%20.%20%7D%0A%7D%0AORDER%20BY%20ASC(%3FitemLabel)'
	url = '%s&format=json' % (url)
	sparql = getURL(url=url)
	json1 = loadSPARQL(sparql=sparql)
	countries = []
	for result in json1['results']['bindings']:
		#print(result)
		q = result['item']['value'].split('/entity/')[1]
		label = result['itemLabel']['value']
		countries.append([label, q])
	return countries

def addImportedFrom(repo='', claim='', lang=''):
	langs = { 'en': 'Q328', 'fr': 'Q8447', 'de': 'Q48183', }
	if repo and claim and lang and lang in langs.keys():
		importedfrom = pywikibot.Claim(repo, 'P143') #imported from
		importedwp = pywikibot.ItemPage(repo, langs[lang])
		importedfrom.setTarget(importedwp)
		claim.addSource(importedfrom, summary='BOT - Adding 1 reference: [[Property:P143]]: [[%s]]' % (langs[lang]))

def addHumanClaim(repo='', item='', lang=''):
	if repo and item and lang:
		print("Adding claim: human")
		claim = pywikibot.Claim(repo, 'P31')
		target = pywikibot.ItemPage(repo, 'Q5')
		claim.setTarget(target)
		item.addClaim(claim, summary='BOT - Adding 1 claim')
		addImportedFrom(repo=repo, claim=claim, lang=lang)

def addGenderClaim(repo='', item='', gender='', lang=''):
	gender2q = { 'female': 'Q6581072', 'male': 'Q6581097' }
	if repo and item and gender and gender in gender2q.keys() and lang:
		print("Adding gender: %s" % (gender))
		claim = pywikibot.Claim(repo, 'P21')
		target = pywikibot.ItemPage(repo, gender2q[gender])
		claim.setTarget(target)
		item.addClaim(claim, summary='BOT - Adding 1 claim')
		addImportedFrom(repo=repo, claim=claim, lang=lang)

def addBirthDateClaim(repo='', item='', date='', lang=''):
	if repo and item and date and lang:
		print("Adding birth date: %s" % (date))
		return addDateClaim(repo=repo, item=item, claim='P569', date=date, lang=lang)

def addDeathDateClaim(repo='', item='', date='', lang=''):
	if repo and item and date and lang:
		print("Adding death date: %s" % (date))
		return addDateClaim(repo=repo, item=item, claim='P570', date=date, lang=lang)

def addDateClaim(repo='', item='', claim='', date='', lang=''):
	if repo and item and claim and date and lang:
		claim = pywikibot.Claim(repo, claim)
		if len(date.split('-')) == 3:
			claim.setTarget(pywikibot.WbTime(year=int(date.split('-')[0]), month=int(date.split('-')[1]), day=int(date.split('-')[2])))
		elif len(date.split('-')) == 2:
			claim.setTarget(pywikibot.WbTime(year=int(date.split('-')[0]), month=int(date.split('-')[1])))
		elif len(date.split('-')) == 1:
			claim.setTarget(pywikibot.WbTime(year=int(date.split('-')[0])))
		item.addClaim(claim, summary='BOT - Adding 1 claim')
		addImportedFrom(repo=repo, claim=claim, lang=lang)

def addOccupationsClaim(repo='', item='', occupations=[], lang=''):
	if repo and item and occupations and lang:
		for occupation in occupations:
			print("Adding occupation: %s" % (occupation.title().encode('utf-8')))
			claim = pywikibot.Claim(repo, 'P106')
			target = pywikibot.ItemPage(repo, occupation.title())
			claim.setTarget(target)
			item.addClaim(claim, summary='BOT - Adding 1 claim')
			addImportedFrom(repo=repo, claim=claim, lang=lang)

def authorIsNewbie(page='', lang=''):
	if page:
		hist = page.getVersionHistory(reverse=True, total=1)
		if hist:
			editcount = getUserEditCount(user=hist[0].user, site='%s.wikipedia.org' % (lang))
			if editcount >= 200:
				return False
	return True

def calculateGender(page='', lang=''):
	if not page:
		return ''
	if lang == 'en':
		femalepoints = len(re.findall(r'(?i)\b(she|her|hers)\b', page.text))
		malepoints = len(re.findall(r'(?i)\b(he|his|him)\b', page.text))
		if re.search(r'(?im)\b(Category\s*:[^\]\|]*?female|Category\s*:[^\]\|]*?women|Category\s*:[^\]\|]*?actresses)\b', page.text) or \
		   (len(page.text) <= 2000 and femalepoints >= 1 and malepoints == 0) or \
		   (femalepoints >= 2 and femalepoints > malepoints*3):
			return 'female'
		elif re.search(r'(?im)\b(Category\s*:[^\]]*? male|Category\s*:[^\]]*? men)\b', page.text) or \
		   (len(page.text) <= 2000 and malepoints >= 1 and femalepoints == 0) or \
		   (malepoints >= 2 and malepoints > femalepoints*3):
			return 'male'
	elif lang == 'de':
		if re.findall(r'(?im)\b(Category|Kategorie)\s*:\s*Frau\s*[\]\|]', page.text):
			return 'female'
		elif re.findall(r'(?im)\b(Category|Kategorie)\s*:\s*Mann\s*[\]\|]', page.text):
			return 'male'
	elif lang == 'fr':
		return '' #todo: ne nee
	return ''

def calculateBirthDate(page='', lang=''):
	if not page:
		return ''
	if lang == 'en':
		m = re.findall(r'(?im)\[\[\s*Category\s*:\s*(\d+) births\s*[\|\]]', page.text)
		if m:
			return m[0]
	elif lang == 'de':
		m = re.findall(r'(?im)\[\[\s*(?:Kategorie|Category)\s*:\s*Geboren (\d+)\s*[\|\]]', page.text)
		if m:
			return m[0]
	elif lang == 'fr':
		m = re.findall(r'(?im)\[\[\s*(?:Catégorie|Category)\s*:\s*Naissance en (?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)? ?(\d+)\s*[\|\]]', page.text)
		if m:
			return m[0]
	return ''

def calculateBirthDateFull(page='', lang=''):
	if not page:
		return ''
	if lang == 'en':
		m = re.findall(r'\{\{(?:B|b)irth (?:D|d)ate and age\|(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)', page.text.replace('|df=yes','').replace('|df=y','').replace('|mf=yes','').replace('|mf=y',''))
		if m:
			return str(m[0][0]) + '-' + str(m[0][1]) + '-' + str(m[0][2])
		m = re.findall(r'\{\{(?:B|b)irth date\|(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)', page.text.replace('|df=yes','').replace('|df=y','').replace(',','').replace('[','').replace(']',''))
		if m:
			try:
				temp = dateparser.parse(str(m[0][0])+' '+str(m[0][1])+' '+str(m[0][2]))
				return str(temp.year) + '-' + str(temp.month) + '-' + str(temp.day)
			except:
				m = False
		if m:
			return str(m[0][0]) + '-' + str(m[0][1]) + '-' + str(m[0][2])
		m = re.findall(r'\|\s*(?:B|b)irth(?:_| )date\s*=\s*(\w+)\s*(\w+)\s*(\w+)', page.text.replace('|df=yes','').replace('|df=y','').replace(',','').replace('[','').replace(']',''))
		if m:
			if len(m[0][0]) + len(m[0][1]) + len(m[0][2]) > 5:
				try:
					temp = dateparser.parse(str(m[0][0])+' '+str(m[0][1])+' '+str(m[0][2]))
					return str(temp.year) + '-' + str(temp.month) + '-' + str(temp.day)
				except:
					m = False
		m = re.findall(r'(?im)\[\[\s*Category\s*:\s*(\d+) births\s*[\|\]]', page.text)
		if m:
			return m[0]
	elif lang == 'de':
		m = re.findall(r'(?im)\|\s*GEBURTSDATUM\s*=\s*(\w+)\s*(\w+)\s*(\w+)', page.text.replace('.',''))
		if m:
			if len(m[0][0]) + len(m[0][1]) + len(m[0][2]) > 5:
				try:
					temp = dateparser.parse(str(m[0][0])+' '+str(m[0][1])+' '+str(m[0][2]))
					return str(temp.year) + '-' + str(temp.month) + '-' + str(temp.day)
				except:
					m = False
		m = re.findall(r'(?im)\[\[\s*(?:Kategorie|Category)\s*:\s*Geboren (\d+)\s*[\|\]]', page.text)
		if m:
			return m[0]
	elif lang == 'fr':
		m = re.findall(r'\{\{(?:D|d)ate sport\|(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)', page.text.replace('|df=yes','').replace('|df=y','').replace('|mf=yes','').replace('|mf=y',''))
		if m:
			return str(m[0][2]) + '-' + str(m[0][1]) + '-' + str(m[0][0])
		m = re.findall(r'\{\{(?:D|d)ate de naissance\|(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)', page.text.replace('|df=yes','').replace('|df=y','').replace('|mf=yes','').replace('|mf=y','').replace('|âge=oui',''))
		if m:
			return str(m[0][2]) + '-' + str(m[0][1]) + '-' + str(m[0][0])
		m = re.findall(r'\{\{(?:D|d)ate de naissance\|(\d+)\s*\|\s*(\w+)\s*\|\s*(\d+)', page.text.replace('|df=yes','').replace('|df=y','').replace('|mf=yes','').replace('|mf=y','').replace('|âge=oui',''))
		if m:
			if len(m[0][0]) + len(m[0][1]) + len(m[0][2]) > 5:
				try:
					temp = dateparser.parse(str(m[0][0])+' '+str(m[0][1])+' '+str(m[0][2]))
					return str(temp.year) + '-' + str(temp.month) + '-' + str(temp.day)
				except:
					m = False
		m = re.findall(r'(?im)\[\[\s*(?:Catégorie|Category)\s*:\s*Naissance en (?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)? ?(\d+)\s*[\|\]]', page.text)
		if m:
			return m[0]
	return ''

def calculateDeathDate(page='', lang=''):
	if not page:
		return ''
	if lang == 'en':
		m = re.findall(r'(?im)\[\[\s*Category\s*:\s*(\d+) deaths\s*[\|\]]', page.text)
		if m:
			return m[0]
	elif lang == 'de':
		m = re.findall(r'(?im)\[\[\s*(?:Kategorie|Category)\s*:\s*Gestorben (\d+)\s*[\|\]]', page.text)
		if m:
			return m[0]
	elif lang == 'fr':
		m = re.findall(r'(?im)\[\[\s*(?:Catégorie|Category)\s*:\s*Décès en (?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)? ?(\d+)\s*[\|\]]', page.text)
		if m:
			return m[0]
	return ''

def calculateDeathDateFull(page='', lang=''):
	if not page:
		return ''
	if lang == 'en':
		m = re.findall(r'\{\{(?:D|d)da\|(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)', page.text.replace('|df=yes','').replace('|df=y','').replace('|mf=yes','').replace('|mf=y',''))
		if m:
			return str(m[0][0]) + '-' + str(m[0][1]) + '-' + str(m[0][2])
		m = re.findall(r'\{\{(?:D|d)eath date and age\|(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)', page.text.replace('|df=yes','').replace('|df=y','').replace('|mf=yes','').replace('|mf=y',''))
		if m:
			return str(m[0][0]) + '-' + str(m[0][1]) + '-' + str(m[0][2])
		m = re.findall(r'\{\{(?:D|d)eath date\|(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)', page.text.replace('|df=yes','').replace('|df=y','').replace(',','').replace('[','').replace(']',''))
		if m:
			if len(m[0][0]) + len(m[0][1]) + len(m[0][2]) > 5:
				try:
					temp = dateparser.parse(str(m[0][0])+' '+str(m[0][1])+' '+str(m[0][2]))
					return str(temp.year) + '-' + str(temp.month) + '-' + str(temp.day)
				except:
					m = False
		m = re.findall(r'\|\s*(?:D|d)eath(?:_| )date\s*=\s*(\w+)\s*(\w+)\s*(\w+)', page.text.replace('|df=yes','').replace('|df=y','').replace(',','').replace('[','').replace(']',''))
		if m:
			if len(m[0][0]) + len(m[0][1]) + len(m[0][2]) > 5:
				try:
					temp = dateparser.parse(str(m[0][0])+' '+str(m[0][1])+' '+str(m[0][2]))
					return str(temp.year) + '-' + str(temp.month) + '-' + str(temp.day)
				except:
					m = False
		m = re.findall(r'(?im)\[\[\s*Category\s*:\s*(\d+) deaths\s*[\|\]]', page.text)
		if m:
			return m[0]
	elif lang == 'de':
		m = re.findall(r'(?im)\|\s*STERBEDATUM\s*=\s*(\w+)\s*(\w+)\s*(\w+)', page.text.replace('.',''))
		if m:
			if len(m[0][0]) + len(m[0][1]) + len(m[0][2]) > 5:
				try:
					temp = dateparser.parse(str(m[0][0])+' '+str(m[0][1])+' '+str(m[0][2]))
					return str(temp.year) + '-' + str(temp.month) + '-' + str(temp.day)
				except:
					m = False
		if not m:
			m = re.findall(r'(?im)\[\[\s*(?:Kategorie|Category)\s*:\s*Gestorben (\d+)\s*[\|\]]', page.text)
			if m:
				return m[0]
	elif lang == 'fr':
		m = re.findall(r'(?im)\[\[\s*(?:Catégorie|Category)\s*:\s*Décès en (?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)? ?(\d+)\s*[\|\]]', page.text)
		if m:
			return m[0]
	return ''

def calculateOccupations(wikisite='', page='', lang=''):
	ignoreoccupations = [
		'Q2066131', #sportpeople, too general
	]
	occupations = []
	if wikisite and page:
		if lang == 'en' or lang == '':
			cats = re.findall(r'(?i)\[\[\s*Category\s*\:([^\[\]\|]+?)[\]\|]', page.text)
		elif lang == 'de':
			cats = re.findall(r'(?i)\[\[\s*(?:Kategorie|Category)\s*\:([^\[\]\|]+?)[\]\|]', page.text)
		elif lang == 'fr':
			cats = re.findall(r'(?i)\[\[\s*(?:Catégorie|Category)\s*\:([^\[\]\|]+?)[\]\|]', page.text)
		for cat in cats:
			cat = cat.strip()
			catpage = pywikibot.Page(wikisite, 'Category:%s' % (cat)) #Category: works for any lang
			catitem = ''
			try:
				catitem = pywikibot.ItemPage.fromPage(catpage)
			except:
				continue
			if not catitem:
				continue
			catitem.get()
			if catitem.claims:
				if 'P4224' in catitem.claims:
					for p4224 in catitem.claims['P4224']:
						if p4224.getTarget().title() != 'Q5':
							continue
						if 'P106' in p4224.qualifiers:
							qualifier = p4224.qualifiers['P106']
							occ = qualifier[0].getTarget()
							if not occ.title() in ignoreoccupations:
								occupations.append(occ)
		occupations = list(set(occupations))
	return occupations

def pageCategories(page='', lang=''):
	if lang == 'en':
		return len(re.findall(r'(?im)\[\[\s*Category\s*\:', page.text))
	elif lang == 'de':
		return len(re.findall(r'(?im)\[\[\s*(?:Kategorie|Category)\s*\:', page.text))
	elif lang == 'fr':
		return len(re.findall(r'(?im)\[\[\s*(?:Catégorie|Category)\s*\:', page.text))
	return 0

def pageReferences(page='', lang=''):
	return len(re.findall(r'(?i)</ref>', page.text))

def pageIsBiography(page='', lang=''):
	if lang == 'en':
		if re.search('(?im)Category\s*:\s*\d+ animal (births|deaths)', page.text):
			return False
		elif not page.title().startswith('List ') and not page.title().startswith('Lists '):
			if len(page.title().split(' ')) <= 5:
				if re.search(r'(?im)(\'{3} \(born \d|Category\s*:\s*\d+ (births|deaths)|Category\s*:\s*Living people|birth_date\s*=|birth_place\s*=|death_date\s*=|death_place\s*=|Category\s*:\s*People from)', page.text):
					return True
	elif lang == 'de':
		if re.search('(?im)(Catégorie|Category)\s*:\s*Individueller', page.text):
			return False
		elif not page.title().startswith('Liste '):
			if len(page.title().split(' ')) <= 5:
				if re.search(r'(?im)((Kategorie|Category)\s*:\s*(Geboren|Gestorben) \d+)', page.text):
					return True
	elif lang == 'fr':
		if re.search('(?im)(Catégorie|Category)\s*:\s*Animal (né|mort)', page.text):
			return False
		elif not page.title().startswith('Liste ') and not page.title().startswith('Listes '):
			if len(page.title().split(' ')) <= 5:
				if re.search(r'(?im)((Catégorie|Category)\s*:\s*(Naissance|Décès) en)', page.text):
					if not re.search(r'(?im)(:(Catégorie|Category)\s*:\s*(Naissance|Décès) en)', page.text):
						return True
	return False

def pageIsRubbish(page='', lang=''):
	if lang == 'en' and re.search(r'(?im)\{\{\s*(db|AfD|Article for deletion|Notability|Prod blp)', page.text):
		return True
	elif lang == 'de' and re.search(r'(?im)\{\{\s*(Löschen|db|SLA|Speedy)', page.text):
		return True
	elif lang == 'fr' and re.search(r'(?im)\{\{\s*(Suppression|À supprimer|Admissibilit[ée]|Avertissement)', page.text):
		return True
	return False

def addBiographyClaims(repo='', wikisite='', item='', page='', lang=''):
	if repo and wikisite and item and page and lang:
		gender = calculateGender(page=page, lang=lang)
		birthdate = calculateBirthDateFull(page=page, lang=lang)
		deathdate = calculateDeathDateFull(page=page, lang=lang)
		occupations = calculateOccupations(wikisite=wikisite, page=page, lang=lang)
		try:
			item.get()
		except:
			print('Error while retrieving item, skiping...')
			return ''
		if not 'P31' in item.claims:
			addHumanClaim(repo=repo, item=item, lang=lang)
		if not 'P21' in item.claims and gender:
			addGenderClaim(repo=repo, item=item, gender=gender, lang=lang)
		if not 'P569' in item.claims and birthdate:
			addBirthDateClaim(repo=repo, item=item, date=birthdate, lang=lang)
		if not 'P570' in item.claims and deathdate:
			addDeathDateClaim(repo=repo, item=item, date=deathdate, lang=lang)
		if not 'P106' in item.claims and occupations:
			addOccupationsClaim(repo=repo, item=item, occupations=occupations, lang=lang)

def main():
	wdsite = pywikibot.Site('wikidata', 'wikidata')
	repo = wdsite.data_repository()
	langs = ['fr']#['en', 'fr', 'de']
	for lang in langs:
		wikisite = pywikibot.Site(lang, 'wikipedia')
		total = 1000
		if len(sys.argv) >= 2:
			total = int(sys.argv[1])
		gen = pagegenerators.NewpagesPageGenerator(site=wikisite, namespaces=[0], total=total)
		#cat = pywikibot.Category(wikisite, 'Category:Articles without Wikidata item')
		#gen = pagegenerators.CategorizedPageGenerator(cat, recurse=False)
		pre = pagegenerators.PreloadingGenerator(gen, groupsize=total)
		for page in pre:
			print(page.title())
			if page.isRedirectPage():
				continue
			if not pageIsBiography(page=page, lang=lang):
				continue
			print('\n==', page.title().encode('utf-8'), '==')
			gender = calculateGender(page=page, lang=lang)
			item = ''
			try:
				item = pywikibot.ItemPage.fromPage(page)
			except:
				pass
			if item:
				print('Page has item')
				print('https://www.wikidata.org/wiki/%s' % (item.title()))
				# test = input('Continue?')
				addBiographyClaims(repo=repo, wikisite=wikisite, item=item, page=page, lang=lang)
			else:
				print('Page without item')
				#search for a valid item, otherwise create
				if authorIsNewbie(page=page, lang=lang):
					print("Newbie author, checking quality...")
					if pageIsRubbish(page=page, lang=lang) or \
					   (not pageCategories(page=page, lang=lang)) or \
					   (not pageReferences(page=page, lang=lang)) or \
					   (not len(list(page.getReferences(namespaces=[0])))):
						print("Page didnt pass minimum quality, skiping")
						continue
				
				print(page.title().encode('utf-8'), 'need item', gender)
				wtitle = page.title()
				wtitle_ = wtitle.split('(')[0].strip()
				searchitemurl = 'https://www.wikidata.org/w/api.php?action=wbsearchentities&search=%s&language=%s&format=xml' % (urllib.parse.quote(wtitle_), lang)
				raw = getURL(searchitemurl)
				print(searchitemurl.encode('utf-8'))
				
				#check birthdate and if it matches, then add data
				numcandidates = '' #do not set to zero
				if not '<search />' in raw:
					m = re.findall(r'id="(Q\d+)"', raw)
					numcandidates = len(m)
					print("Found %s candidates" % (numcandidates))
					if numcandidates > 5: #too many candidates, skiping
						print("Too many, skiping")
						continue
					for itemfoundq in m:
						itemfound = pywikibot.ItemPage(repo, itemfoundq)
						itemfound.get()
						if ('%swiki' % (lang)) in itemfound.sitelinks:
							print("Candidate %s has sitelink, skiping" % (itemfoundq))
							numcandidates -= 1
							continue
						pagebirthyear = calculateBirthDate(page=page, lang=lang)
						pagebirthyear = pagebirthyear and int(pagebirthyear.split('-')[0]) or ''
						if not pagebirthyear:
							print("Page doesnt have birthdate, skiping")
							break #break, dont continue. Without birthdate we cant decide correctly
						if 'P569' in itemfound.claims and itemfound.claims['P569'][0].getTarget().precision in [9, 10, 11]:
							#https://www.wikidata.org/wiki/Help:Dates#Precision
							itemfoundbirthyear = int(itemfound.claims['P569'][0].getTarget().year)
							print("candidate birthdate = %s, page birthdate = %s" % (itemfoundbirthyear, pagebirthyear))
							mindatelen = 4
							if len(str(itemfoundbirthyear)) != mindatelen or len(str(pagebirthyear)) != mindatelen:
								print("%s birthdate length != %s" % (itemfoundq, mindatelen))
								continue
							#reduce candidates if birthyear are different
							minyeardiff = 3
							if itemfoundbirthyear >= pagebirthyear + minyeardiff or itemfoundbirthyear <= pagebirthyear - minyeardiff:
								print("Candidate %s birthdate out of range, skiping" % (itemfoundq))
								numcandidates -= 1
								continue
							#but only assume it is the same person if birthyears match
							if itemfoundbirthyear == pagebirthyear:
								print('%s birthyear found in candidate %s. Category:%s births found in page. OK!' % (itemfoundbirthyear, itemfoundq, itemfoundbirthyear))
								# test = input('Continue?')
								print('Adding sitelink %s:%s' % (lang, page.title().encode('utf-8')))
								try:
									itemfound.setSitelink(page, summary='BOT - Adding 1 sitelink: [[:%s:%s|%s]] (%s)' % (lang, page.title(), page.title(), lang))
								except:
									print("Error adding sitelink. Skiping.")
									break
								# test = input('Continue?')
								addBiographyClaims(repo=repo, wikisite=wikisite, item=itemfound, page=page, lang=lang)
								break
				
				#no item found, or no candidates are useful
				if '<search />' in raw or (numcandidates == 0):
					print('No useful item found. Creating a new one...')
					# test = input('Continue?')
					#create item
					newitemlabels = { lang: wtitle_ }
					newitem = pywikibot.ItemPage(repo)
					newitem.editLabels(labels=newitemlabels, summary="BOT - Creating item for [[:%s:%s|%s]] (%s): %s %s" % (lang, wtitle, wtitle, lang, 'human', gender))
					newitem.get()
					try:
						newitem.setSitelink(page, summary='BOT - Adding 1 sitelink: [[:%s:%s|%s]] (%s)' % (lang, page.title(), page.title(), lang))
					except:
						print("Error adding sitelink. Skiping.")
						break
					addBiographyClaims(repo=repo, wikisite=wikisite, item=newitem, page=page, lang=lang)
					exit()

if __name__ == "__main__":
	main()

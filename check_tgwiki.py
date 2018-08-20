#!/usr/bin/python
# -*- coding: utf-8  -*-
# Try to auto-populate family names
# Mike Peel     09-Jun-2018      v1 - start

from __future__ import unicode_literals

import pywikibot
import numpy as np
import time
import string
from pywikibot import pagegenerators
import urllib
import csv

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

stepsize =  1000
maximum = 10000000
numsteps = int(maximum / stepsize)

wikidata_site = pywikibot.Site("wikidata", "wikidata")
repo = wikidata_site.data_repository()  # this is a DataSite object
debug = 1

def update_report(qid):
    report = pywikibot.Page(wikidata_site, 'User:Mike Peel/tgwiki sitelink problems')
    report_text = report.get()
    rep = u'\n*{{Q|'+str(qid)+'}}'
    if rep in report_text:
        return
    report.text = report_text + rep
    report.save('Update report to include ' + qid)
    return

# # Read in the family names database
# with open('populate_family_names_cache.csv', mode='r') as infile:
#     reader = csv.reader(infile)
#     with open('coors_new.csv', mode='w') as outfile:
#         writer = csv.writer(outfile)
#         names = {rows[1]:rows[0] for rows in reader}
# print names

for i in range(0,numsteps):
    print 'Starting at ' + str(i*stepsize)

    query = 'SELECT ?item ?itemLabel ?article\n'\
    'WHERE\n'\
    '{\n'\
    '    ?article    schema:about ?item ;\n'\
    '            schema:isPartOf <https://tg.wikipedia.org/> .\n'\
    '    SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],tg" }\n'\
    '}\n'\
    'LIMIT ' + str(stepsize) + ' OFFSET ' + str(i*stepsize)
    print query
    # exit()
    i = 0
    generator = pagegenerators.WikidataSPARQLPageGenerator(query, site=wikidata_site)
    for page in generator:
        try:
            item_dict = page.get()
            qid = page.title()
        except:
            print 'Huh - no page found'
            continue
        print "\n" + qid
        try:
            tgwp = item_dict['sitelinks']['tgwiki']
            print tgwp
        except:
            print 'tgwiki sitelink not found!'
            continue

        print tgwp.decode('utf-8')


        url = u'https://tg.wikipedia.org/wiki/'+tgwp.replace(' ','_')
        url = urllib.quote(url.encode('utf8'), ':/')
        print url
        #tgwp.decode('unicode-escape').encode('utf-8') #.decode('unicode_escape')#.encode('utf8')
        #url = urllib.quote(url, safe="%/:=&?~#+!$,;'@()*[]")

        a=urllib.urlopen(url)
        code = a.getcode()
        print code
        if code == 404:
            update_report(qid)

# EOF
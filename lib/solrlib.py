# a bunch of apache solr functions
import pysolr
from datetime import datetime

# Create a client instance. The timeout and authentication options are not required.
solr = pysolr.Solr('https://tal.lipn.univ-paris13.fr/solr8/phc_climat/', always_commit=True)

# Do a health check.
solr.ping()


# For a more advanced query, say involving highlighting, you can pass
# additional options to Solr.
#results = solr.search('bananas', **{
#    'hl': 'true',
#    'hl.fragsize': 10,
#})



def solr_search_all(query, rows, cursorMark):
	params = {'rows':rows, "fl": "contents,link", 'sort':'url desc', 'cursorMark':cursorMark} # sort => 'id asc',
	done = False
	while done != True:
		results = solr.search(query, **params)
		#print(results.raw_response)
		if params['cursorMark'] == results.nextCursorMark:
			done = True
		params['cursorMark'] = results.nextCursorMark
		yield (results.docs, solr_search_all(query,rows, cursorMark))
	
query = 'contents:biodiversité'
rows = 1000
cursorMark='*'
allresults = []
total = 0
start = datetime.now()
for res, gen in solr_search_all(query, rows, cursorMark):
    allresults.append(res)
    print(res)
    total = total+ len(res)
#print(allresults, len(allresults), total)
end = datetime.now()
time_taken = end - start
print('Time (1000 rows): ',time_taken) 

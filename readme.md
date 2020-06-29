# neoveille2020
Rewriting of neoveille2016 (python, parameterized backend pipelines)


This directory contains two main programs :
- ```corpus_crawler.py``` :  main program to retrieve corpora from websites, rss feeds and local files
- ``` corpus_analysis.py ``` : main program to analyze corpora (from several sources : solr query, web page(s), local file(s)), ie morphological analysis and formal neologism detection.

these programs constitute the backend of the Neoveille platform. The frontend web site enables to interact with the results, and to configure several aspects (corpora handling, neologism editing, etc.).

# Installation

First ensure you have a working Mysql server installed and running, and Apache Solr running with a working collection (a remote Apache Solr server is also possible).

To make these program work, you need at least python 3.7.

First clone the repository.

Then, install Python modules :

```
pip install -r requirements.txt
```



# Usage

You must first tune a configuration file before running the main program. Here is an example file (```config/settings.local.fr.treetagger.ini```):

```Python

[GENERAL]
# generic parameters
lang = french
lang_iso=fr
# data source (either solr_query, mysql_query, local_files, webpage, csv, etc.)
data_source=solr_query
# either spacy, hunspell, spacy+exclusiondico, treetagger, treetagger+exclusiondico, udpipe, udpipe+exclusiondico
ling_pipeline = treetagger+pattern+exclusiondico+hunspell
# where to save outputs (solr, db, solr+db)
#solr+db+file
analysis_output=file
# fields to save/output for each doc (from apache solr schema) - NOT USED YET
output_doc_fields=pos-text,neologismes



[MYSQL]
# global variables for mysql connection (useful only if db implied in processes)
user=root
password=root
host=localhost
# database where data sources are defined (default table : RSS_INFO)
db_corpus=rssdata
# database where exclusion dico is defined 
db_dico=datatables
# database where candidate neologisms must be stored (default table : neologismes_<lang_iso>)
db_neo=datatables

[SOLR]
# global variables for Apache Solr url (useful only if solr implied in processes)
# host
solr_host = https://tal.lipn.univ-paris13.fr/solr/
# name of collection
solr_collection=rss_french
# path to schema (not used yet but useful to determine correspondance between rss-feeds fields and solr target fields)
solr_schema=
# input data (in case of data_type_method=solr) : any solr query will work (hopefully...)
# source:"Le Figaro" && dateS:[NOW-1YEAR TO NOW]
input_solr_query=contents:végétalien && dateS:[NOW-1YEAR TO NOW]


[LANG_DETECT]
# language code for lang detection (ISO 639-1 codes : https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes)
# is a list (ie : 'en, nl')
lang_detect=fr


[JUSTEXT]
# stoplist for justext
stoplist=French

[SPACY]
# specific for spacy depending on ling_analysis method
# warning : you have to launch server independently
spacy_server=http://127.0.0.1:5000
model=fr_core_news_sm
token_tags=text, lemma, pos, is_oov

[HUNSPELL]
# main dictionary + affix (required) : https://github.com/wooorm/dictionaries
main_dict=/Users/emmanuelcartier/Desktop/GitHub/neoveille/neoveille-dev/resources/hunspell/hunspell-dicos/france/fr_FR
# additional dictionary (optional)
add_dict=
# word filter as re (ie to skip capitalized words) (optional)
pre_filter=[\w-]{4,}

# TBD : not used yet
[TREETAGGER]
# specific for Treetager depending on ling_analysis method
#  treetagger server
# warning :you have to launch server independently
treetagger_server=http://127.0.0.1:5055

# neologisms patterns
[NEOLOGISMS]
# specific constraints on neologisms detection 
# regular expression patterns \w{3,}(?:-\w{3,}){0,3}
pattern =[\w-]{3,}
# excluded dico service url
excluded_dico_server=http://127.0.0.1:5056


```

The [GENERAL] section contains the main parameters of the program:
- the language of the corpora
```
lang = french
lang_iso=fr
```

- the data source (either solr_query, mysql_query, local_files, webpage, csv, etc.)
```
data_source=solr_query
```

- the linguistic pipeline : either spacy, hunspell, treetagger, exclusiondico, or a combination of them
```
ling_pipeline = treetagger+pattern+exclusiondico+hunspell
```

- the output of analysis (either solr, db, file or a combination of them)
```
output=solr+db+file
```


The other sections correspond to sub-components.


As can be noted in the configuration file, several components are web services and must be launched before launching the main program.
Notably : 
- ```./lib/treetagger_server.py ```: this web service needs Treetagger installed and the root directory informed
- ``` ./lib/spacy_server.py``` :  this web service needs Spacy installed
- ```./lib/excluded_dico_server.py``` : it enables to check if candidate neologisms pertain or not to a reference dictionary.

Once these settings are OK and web services launched, you can run the main program ```python corpus_analysis.py <configuration_file>```

For example :
```
python corpus_crawl_and_analysis.py config/settings.local.fr.treetagger.ini
```

The program will load the configuration file and check if configuration components are available. then it will analyze the documents 
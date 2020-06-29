# neoveille2020
Rewriting of neoveille2016 (python 3 , configuration file to update and extend input source files, linguistic pipelines and results output)


This directory contains two main programs :
- ```corpus_crawler.py``` :  main program to retrieve corpora from websites, rss feeds and local files
- ``` corpus_analysis.py ``` : main program to analyze corpora (from several sources : solr query, web page(s), local file(s)), ie morphological analysis and formal neologism detection.

these programs constitute the backend of the Neoveille platform. The frontend web site enables to interact with the results, and to configure several aspects (corpora handling, neologism editing, etc.).

# Installation

First ensure you have an Apache Solr available and running with a working collection (a remote Apache Solr server is also possible).

To make these program work, you need at least python 3.7.

First clone the repository:
```
git clone https://github.com/ecartierlipn/neoveille2020.git
```

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
# global variables for Apache Solr url (useful only if solr is implied in processes)
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


[JUSTEXT] useless for corpus_analysis.py
# stoplist for justext
stoplist=French

[SPACY] only if you include spacy in the linguistic pipeline
# specific for spacy depending on ling_analysis method
# warning : you have to launch server independently
spacy_server=http://127.0.0.1:5000
model=fr_core_news_sm
token_tags=text, lemma, pos, is_oov

[HUNSPELL] only if you include hunspell in the linguistic pipeline
# main dictionary + affix (required) : https://github.com/wooorm/dictionaries
main_dict=/Users/emmanuelcartier/Desktop/GitHub/neoveille/neoveille-dev/resources/hunspell/hunspell-dicos/france/fr_FR
# additional dictionary (optional)
add_dict=
# word filter as re (ie to skip capitalized words) (optional)
pre_filter=[\w-]{4,}


[TREETAGGER] only if you include treetagger in the linguistic pipeline
# specific for Treetager depending on ling_analysis method
#  treetagger server
# warning :you have to launch server independently
treetagger_server=http://127.0.0.1:5055

# neologisms patterns
[NEOLOGISMS] only if you include neologisms excluded dico and re patterns in the linguistic pipeline
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
analysis_output=solr+db+file
```


The other sections correspond to sub-components.


As can be noted in the configuration file, several components are web services and must be launched before launching the main program.
Notably : 
- ```./lib/treetagger_server.py ```: this web service needs Treetagger installed and the root directory informed in the file. For full installation instructions, see : https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/.
- ``` ./lib/spacy_server.py``` :  this web service needs Spacy installed. see full doc here : https://spacy.io/usage.
- ```./lib/excluded_dico_server.py``` : it enables to check if candidate neologisms pertain or not to a reference dictionary. Necessary if you would like to use a reference dictionary saved in a mysql db.

Once these settings are OK and web services launched, you can run the main program ```python corpus_analysis.py <configuration_file>```

For example :
```
python corpus_crawl_and_analysis.py config/settings.local.fr.treetagger.ini
```

The program will load the configuration file and check if configuration components are available. then it will analyze (ling_pipeline parameter) the documents (data_source parameter) and save the results according to the analysis_output parameter.
A log file is generated in the logs subdirectory. 
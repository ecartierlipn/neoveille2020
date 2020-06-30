#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
program to retrieve articles from rss feeds (and potentially other web sources)
See main() function for details - Python 2.7+
'''
import os,sys,re,time
from datetime import datetime
import configparser
import mysql.connector
from mysql.connector import Error
import logging
import logging.config
import pickle,json
import pysolr

# nlp modules
from unidecode import unidecode
from langdetect import detect
#from hunspell import Hunspell
from transformers import BertTokenizer
PRE_TRAINED_MODEL_NAME = 'bert-base-cased'
tokenizer = BertTokenizer.from_pretrained(PRE_TRAINED_MODEL_NAME)

import lib.spacy_client as spacy_client
import lib.treetagger_client as treetagger_client
import lib.excluded_dico_client as excluded_dico_client
import lib.hunspell_client as hunspell_client

class corpus:
    """classe corpus pour gerer les corpus : il suffit de donner la langue, et eventuellement où se trouve la source (db, file),
    et le type de corpus (rss, web twitter) - les deux derniers sont à developper
    """
    def __init__(self, lang, lang_iso,data_source,ling_config, output_type):
        "construit une instance avec les attributs de base"
        self.lang = lang
        self.lang_iso = lang_iso
        self.data_source = data_source
        self.ling_config= ling_config
        self.output_type= output_type
        self.corpusitems = []

    def analyse_corpus(self):
        """main method to retrieve corpus data"""
        log.info("retrieving source corpus")
        if self.data_source == 'solr_query':
            query = input_solr_query
            rows = 1000
            cursorMark='*'
            # just an utility to get all detected neologisms and the docs
            neodocs={}
            # launch generator function : res is a bunch of results from solr (array of dict containing id/url + contents (other fields are discarded here) retrieved by corpus_spider.py)
            for res, gen in solr_search_all(query, rows, cursorMark):
                #analyse each doc in res according to self.ling_config
                for doc in res:
                    # lang detection
                    print("Analysing : " + doc['link'])
                    #log.info(doc['link'])
                    langd = detect(doc['contents'][0])
                    if (langd not in self.ling_config['lang_detect']):
                        log.warning("Problem with language detection for contents : " + str(doc['contents']) +
                                "\nAutomatic detection says : [" + str(langd) + "] whereas expected language is " +
                                str(self.ling_config['lang_detect']) + "\nSkipping analysis for this document and deleting it from database.")
                        continue
                    # BertWordPiece tokenizer : cleaning and reconstitution of tokenized text
                    tokens = tokenizer.tokenize(doc['contents'][0])
                    doctokens = re.sub(r"## ","",re.sub(r" ##",''," ".join(tokens)))
                    log.info(doctokens)
                    doc['contents']=doctokens
                    oov=[]
                    #log.info("parsing " + str(doc))
                    # SPACY
                    if 'spacy' in self.ling_config['type']:
                        # res of the form {'tokens': tokens},{'lemmapos': lemmapos},{'oov': oov},{'ne': entities}
                        ling_analysis = spacy_client.get_nlp(self.ling_config['spacy_server'], doc['contents'])
                        #print(ling_analysis)
                        if ling_analysis:
                            doc['pos-text'] = ling_analysis[1]['lemmapos']
                            oov = ling_analysis[1]['oov'].keys()
                            log.info("List of unknown words / neologisms after Spacy: " + str(oov))
                            #log.info(doc['pos-text'])

                    # TREETAGGER
                    elif 'treetagger'  in self.ling_config['type']:
                        # linguistic analysis {'tokens': tokens},{'lemmapos': lemmapos},{'oov': oov},{'ne': entities}
                        ling_analysis = treetagger_client.get_nlp_and_unk(self.ling_config['treetagger_server'], doc['contents'])
                        log.info(ling_analysis)
                        if ling_analysis:
                            taggedtext = ling_analysis['taggedtext']
                            oov = ling_analysis['unknown'].keys()
                            doc['pos-text'] = " ".join([k for k in taggedtext])
                            #doc['neologismes'] = " ".join([k for k in oov.keys()])
                            log.info("List of unknown words / neologisms after treetagger: " + str(oov))
                            # save neodoc if just treetagger
                    
                    
                    # neologisms pattern
                    if 'pattern' in self.ling_config['type']:
                        oov2 = []
                        # check neo_pattern
                        for neo in oov:
                            wordinfo = neo.split("\t")
                            #word1 = unidecode(wordinfo[0].strip().lower())
                            word2 = unidecode(wordinfo[0].strip().replace('-',''))
                            if (re.match(self.ling_config['neo_pattern'],word2)) and (word2.islower()) and (not(re.search(r'\d', word2))):
                                oov2.append(neo)
                        oov = oov2
                        log.info("List of neologism after pattern match: " + str(oov))
                    
                    # exclusion dico check
                    if 'exclusiondico' in self.ling_config['type']:
                        oov2 = []
                        # check neo_pattern
                        for neo in oov:
                            wordinfo = neo.split("\t")
                            word1 = unidecode(wordinfo[0].strip().lower())
                            #word2 = unidecode(wordinfo[0].strip().replace('-',''))
                            if excluded_dico_client.get_entry(self.ling_config['excluded_dico_server'],word1,lang_iso) is False:
                                oov2.append(neo)
                        oov = oov2
                        log.info("List of neologism after exclusiondico: " + str(oov))

                    # spell checker
                    if 'hunspell' in self.ling_config['type']:
                        oov2 = []
                        for neo in oov:
                            (res, info)=hunspell_client.hunspell_check_word(neo.split("\t")[0], ling_config['hunspell']['main_dict'])
                            if res is True:
                                oov2.append(neo)
                            # with hunspell library
                            #suggests = hunspell.suggest(neo)
                            #if len(suggests)>0 and suggests[0] != neo:
                            #    oov2.append(neo)
                        oov = oov2
                        log.info("List of neologism after hunspell spell checker : " + str(oov))
                            
                    # finally add to main neologisms dict = word : {'files':[files], 'suggestions':''})
                    # and update doc['neologismes'] for solr update
                    doc['neologismes'] = " ".join([k for k in oov])
                    for neo in oov:
                        docs = neodocs.get(neo,[])
                        docs.append(doc['link'])
                        neodocs[neo]=docs
                            
                    # outputs
                    # to solr
                    if 'solr' in self.output_type:
                        update_to_SOLR(doc)
                        log.info(doc)

            log.info("All articles parsed.")
            log.info("Detected Neologisms : " + str(neodocs))
            print("All data sources parsed.")
            print("Detected Neologisms : " + str(neodocs))
            if 'file' in self.output_type:
                with open('./output/corpus_analysis.py.log.' + start.strftime('%Y-%m-%d_%H:%M:%S') + '.neologisms.txt',mode="w", encoding="utf-8") as fout:
                    json.dump(neodocs, fout, indent=4)
        # to be done
        elif self.data_source=='twitter':
            #retrieve_twitter(self.twitterconfig)
            return True
        elif self.data_source=='url':
            #analyse_doc(self.twitterconfig)
            return True
        # to be done
        elif self.data_source=='local_doc':
            #analyse_doc(self.path)
            return True
        else:
            return False
          

            
################################# solr functions
        
def solr_search_all(query, rows, cursorMark):
    params = {'rows':rows, 'fl': "contents,link",'sort':'link desc', 'cursorMark':cursorMark} # sort => 'id asc',
    done = False
    while done != True:
        results = solr.search(query, **params)
		#print(results.raw_response)
        if params['cursorMark'] == results.nextCursorMark:
            done = True
        params['cursorMark'] = results.nextCursorMark
        yield (results.docs, solr_search_all(query,rows, cursorMark))
	
def update_to_SOLR(res):
    ''' update doc in solr with linguisic analysis'''
    try:
        resp = solr.add([res],fieldUpdates={'pos-text':'set','neologismes':'set'}, commit=True)
        log.info(resp)
        return True
    except Exception as e:
        log.info("Error updating document to Apache Solr :" + str(e))
        return False

def get_SOLR_collection_info():
    ''' get solr collection info with pysolr'''
    try:
        solr = pysolr.Solr(solr_host+ solr_collection, search_handler='/schema/fields', use_qt_param=False)
        #solr =  pysolr.Solr(solr_host+ solr_collection) #, always_commit=True
        #solr_res = solr.results_cls
        #log.info()
        resp = solr._send_request('get', '/schema/fields')
        #log.info(resp)
        json_resp = json.loads(resp)
        #log.info(json_resp)
        for field in json_resp['fields']:
            log.info(field)
    except Exception as e:
        log.error("Error searching schema info -  Apache Solr :" + str(e))

# output / save function
def save_corpus_analysis_to_DB(res,lang_iso):
    """ Save rss corpus to database - just links, country information (for use to check already retrieved web pages) """
    log.info("Saving rss corpus to database")
    try:
        conn = mysql.connector.connect(host=mysqlhost,
                                       database=mysqldb_corpus,
                                       user=mysqluser,
                                       password=mysqlpassword,
                                       charset='utf8mb4',
                                       collation='utf8mb4_general_ci',
                                       autocommit=True)
        
        cursor=conn.cursor()
        if conn.is_connected():
            str=''
            for rss in res:
                if len(rss['link'])>255:
                    rss['link'] = rss['link'][0:254]
                args = [rss['link'],lang_iso,0]
                results = cursor.callproc('ADD_RSS_DATA', args)
                if results:
                    log.info("Article saved to DB" + rss['link'])
                else:
                    log.error("Problem with this article " + str(results))

    except mysql.connector.Error as e:
        log.error(e.errno)
        log.error(e.sqlstate)
        log.error(e.msg)
        return False

    finally:
        cursor.close()
        conn.close()


    """ add neologisms to database for web interface validation """
    log.info("Saving neologisms to database" + str(neolist) + ' : and info : ' + str(neosinfo))
    #for  neo in neolist:
    #    log.info("Saving neologism : " + neo + " : " + str(len(neolist[neo])) + ' : ' + neosinfo.get(neo,'spacy:oov'))

    proc_name = 'ADD_NEOLOGISM_' + lang 
    log.info("Saving with procedure : " + proc_name)
    try:
        conn = mysql.connector.connect(host=mysqlhost,
                                       database=mysqldb_neo,
                                       user=mysqluser,
                                       password=mysqlpassword,
                                       autocommit=True)
        if conn.is_connected():
            for neo in neolist.keys():
                #log.info("Saving neologism : " + neo + " : " + str(len(neolist[neo])) + ' : ' + neosinfo.get(neo,'spacy:oov'))
                args=[neo, len(neolist[neo]), neosinfo.get(neo,'spacy:oov'), 0]
                log.info("Saving neologism with following data : " + str(args))
                cursor = conn.cursor()
                results = cursor.callproc(proc_name, args)
                log.info(str(results )+ "\n")
                cursor.close()

    except Error as e:
        log.warning(str(e))
        return False

    finally:
        conn.close()
        return Tru

# main method
def main(): 
    
    #get_SOLR_collection_info()
    #exit()
    print("Lauching file analysis")
    log.info("Initializing corpus analysis width following paramaters:\nLang : " + lang + "\nData source : " + str(data_source) + "\nLinguistic config : " + str(ling_config) + "\nOutput : " + str(output_type))
    print("Initializing corpus analysis width following paramaters:\nLang : " + lang + "\nData source : " + str(data_source) + "\nLinguistic config : " + str(ling_config) + "\nOutput : " + str(output_type))
    c = corpus(lang,lang_iso,data_source,ling_config,output_type) # initialisation corpus avec info langue, input data type, ling_config and output
    log.info(" retrieving corpus from corpus class" )
    c.analyse_corpus()


# main
if __name__ == '__main__':
    start = datetime.now()
    print("Starting corpus analysis : "+ start.strftime('%Y-%m-%dT%H:%M:%S'))
    os.makedirs('./log', exist_ok=True)
    os.makedirs('./output', exist_ok=True)
    
    # loading configuration file
    if len(sys.argv)<2:
        print("Please indicate the configuration file as an argument! Exiting.")
        exit()
    configfile = sys.argv[1]
    print("Loading configuration for analysis from :" + configfile)
    # logger
    log = logging.getLogger(__name__) 
    logging.basicConfig(filename='log/corpus_analysis.py.log.' + start.strftime('%Y-%m-%d') + '.txt', level=logging.INFO, format='%(levelname)s:%(asctime)s -- [%(filename)s:%(lineno)s - %(funcName)s()] -- %(message)s', filemode="w")
    print("Logging file : " + 'log/corpus_analysis.py.log.' + start.strftime('%Y-%m-%d') + '.txt')
    # read configfile
    #print("reading configuration file :" + configfile)
    log.info("reading configuration file :" + configfile)
    config = configparser.ConfigParser()
    config.read(configfile)
    # general parameters
    lang = config['GENERAL']['lang']
    lang_iso=config['GENERAL']['lang_iso']
    ling_pipeline = config['GENERAL']['ling_pipeline'].strip().split('+')
    data_source = config['GENERAL']['data_source']
    output_type = config['GENERAL']['analysis_output'].strip().split('+')
        
    
    # mysql parameters
    if 'MYSQL' in config:
        mysqluser=config['MYSQL']['user']
        mysqlpassword=config['MYSQL']['password']
        mysqlhost=config['MYSQL']['host']
        mysqldb_corpus=config['MYSQL']['db_corpus']
        mysqldb_neo=config['MYSQL']['db_neo']
        mysqldb_dico=config['MYSQL']['db_dico']
        # to be done : check availability of mysql server
    
    # Apache Solr parameters
    solr_host = config['SOLR']['solr_host']
    solr_collection = config['SOLR']['solr_collection']
    solr_schema = config['SOLR']['solr_schema']
    if data_source =='solr_query':
        input_solr_query = config['SOLR']['input_solr_query']
    # launch solr instance
    solr =  pysolr.Solr(solr_host+ solr_collection, always_commit=True)

    
    # ling_analysis 
    ling_config={}
    # lang detect
    # can be a list (ie : 'en, nl')
    ling_config['lang_detect']=[x.strip() for x in config['LANG_DETECT']['lang_detect'].split(',')] # list of acceptable guessing for the given language
 
    # hunspell
    if 'hunspell' in ling_pipeline:
        ling_config['hunspell']={}
        ling_config['hunspell']['main_dict']=config['HUNSPELL']['main_dict']
        try:
            if os.path.exists(ling_config['hunspell']['main_dict'] + '.dic') is False :
                print("Hunspell path to dictionary is not functionning (" + ling_config['hunspell']['main_dict'] + "). Check your path (default : ling_resources/hunspell-dicos/[france/fr_FR])  to .dic and .aff files and re-run. Exiting.")
                log.error("Hunspell path to dictionary is not functionning (" + ling_config['hunspell']['main_dict'] + "). Check your path (default : ling_resources/hunspell-dicos/[france/fr_FR]) to .dic and .aff files and re-run. Exiting.")
                exit()
            # to check if hunspell installed
            cmd_exists = lambda x: any(os.access(os.path.join(path, x), os.X_OK) for path in os.environ["PATH"].split(os.pathsep))
            if cmd_exists('hunspell') is False:
                print("Hunspell is not installed on your machine. Install it (https://github.com/hunspell/hunspell) and retry. Exiting.")
                log.error("Hunspell is not installed on your machine. Install it (https://github.com/hunspell/hunspell) and retry. Exiting.")
                exit()
                
            # with hunspell library : hunspell = Hunspell(lang_iso + '_'+ lang_iso.upper(), d)
            #hunspell_client.hunspell_check_word("a", ling_config['hunspell']['main_dict'])
            print("Hunspell spell checker installed and working on this machine.")
            log.info("Hunspell spell checker installed and working on this machine.")
        except Exception as e:
            log.exception('Problem initializing Hunspell dictionary from path given / other problem arising linked to hunspell dict')
            print('Problem initializing Hunspell dictionary from path given / other problem arising linked to hunspell dict. Check log file. ')
            exit()
        if len(config['HUNSPELL']['add_dict'])>0:
            ling_config['hunspell']['add_dict']=config['HUNSPELL']['add_dict']
            #try:
            #    hunspell.add_dic(ling_config['hunspell']['add_dict'])
            #except Exception as e:
            #    log.exception('Problem initializing Hunspell additional dictionary from path given.')
            #    exit()
        if len(config['HUNSPELL']['pre_filter'])>0: 
            ling_config['hunspell']['pre_filter']=config['HUNSPELL']['pre_filter']
            
    # exclusiondico
    if 'exclusiondico' in ling_pipeline:
        if not 'excluded_dico_server' in config['NEOLOGISMS']:
            log.error("Excluded dico server not available. Check config file and add an url for key 'excluded_dico_server' in NEOLOGIMS section. Exiting.")
            print("Excluded dico server not available. Check config file and add an url for key 'excluded_dico_server' in NEOLOGIMS section. Exiting.")
            exit()
        else:
            ling_config['excluded_dico_server']=config['NEOLOGISMS']['excluded_dico_server']
            # excluded dico web service check
            if excluded_dico_client.check_server(ling_config['excluded_dico_server']) is False:
                log.error("Excluded dico server not available. Check the server is running (lib/excluded_dico_server.py <list of lang is codes>). Exiting.")
                print("Excluded dico server not available. Check the server is running (lib/excluded_dico_server.py <list of lang iso codes>). Exiting.")
                exit()
            elif excluded_dico_client.check_lang(ling_config['excluded_dico_server'],lang_iso) is False: 
                log.error("Excluded dico server not available for language " + lang_iso + ". Relaunch server (lib/excluded_dico_server.py <list of lang is codes>) with this language. Exiting.")
                print("Excluded dico server not available for language " + lang_iso + ". Relaunch server (lib/excluded_dico_server.py <list of lang iso codes>) with this language. Exiting.")
                exit()
            else:
                log.info("Excluded dico server running and available for langugage : " + lang_iso)
                print("Excluded dico server running and available for langugage : " + lang_iso)
                    

            
    # SPACY
    if 'spacy' in ling_pipeline:
        ling_config['type']=ling_pipeline
        ling_config['spacy_server']=config['SPACY']['spacy_server']
        ling_config['model']=config['SPACY']['model']
        ling_config['token_tags']=[x.strip() for x in config['SPACY']['token_tags'].split(',')]
        from lib.spacy_client import get_nlp,check_server, check_model
        res = check_server(ling_config['spacy_server'])
        if res is False:
            log.error("Spacy server (lib/spacy_server.py <iso_lang>) is not running. Please launch it before running this file. Exiting.")
            print("Spacy server (lib/spacy_server.py <iso_lang>) is not running. Please launch it before running this file. Exiting.")
            exit()
        else:
            # check model
            res = check_model(ling_config['spacy_server'],lang_iso)
            if res is False:
                log.error("Spacy server model not corresponding to language [" + lang_iso + "]. Launch it again (lib/spacy_server.py <iso_lang>) with the current language. Exiting.")
                print("Spacy server model not corresponding to language [" + lang_iso + "]. Launch it again (lib/spacy_server.py <iso_lang>) with the current language. Exiting.")
                exit()
            else:
                log.info("Spacy server check OK.")
                print("Spacy server check OK.")
    # TREETAGGER
    if 'treetagger' in ling_pipeline:
        ling_config['type']=ling_pipeline
        ling_config['treetagger_server']=config['TREETAGGER']['treetagger_server']
        # check treetagger server is running
        res = treetagger_client.check_server(ling_config['treetagger_server'])
        if res is False:
            log.error("Treetagger server (lib/treetagger_server.py <iso_lang>) is not running. Please launch it before running this file. Exiting.")
            print("Treetagger server (lib/treetagger_server.py <iso_lang>) is not running. Please launch it before running this file. Exiting.")
            exit()
        else:
            # check model language
            res = treetagger_client.check_lang(ling_config['treetagger_server'],lang_iso)
            if res is False:
                log.error("Treetagger server language not corresponding to language [" + lang_iso + "]. Launch it again (lib/treetagger_server.py <iso_lang>) with the current language. Exiting.")
                print("Treetagger server language not corresponding to language [" + lang_iso + "]. Launch it again (lib/treetagger_server.py <iso_lang>) with the current language. Exiting.")
                exit()
            else:
                log.info("Treetagger server and language model check OK.")
                print("Treetagger server and language model check OK.")
    
    # NEOLOGISMS PATTERN
    if 'pattern' in ling_pipeline:
        regexp = config['NEOLOGISMS']['pattern'].strip()
        ling_config['neo_pattern']=regexp

    
    main()
else:
    log = logging.getLogger(__name__)

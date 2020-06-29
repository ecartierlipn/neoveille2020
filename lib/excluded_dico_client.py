import requests,logging
from unidecode import unidecode

log = logging.getLogger(__name__)

def check_server(url):
    '''Function to check Excluded dicos server available'''
    try:
        response = requests.get(url + '/check')
        log.info(response.json())
        if response.raise_for_status(): # bad response
            log.error(response.raise_for_status())
            return False
        else:
            return True
    except Exception as e:
        log.error("Error with Excluded dicos server : " + str(e))
        return False

def check_lang(url,lang):
    '''Function to check Excluded dicos server lang'''
    try:
        response = requests.post(url + '/check_lang', data={'lang':lang})
        log.info(response.json())
        if response.raise_for_status(): 
            log.error(response.raise_for_status())
            return False
        else:
            return True
    except Exception as e:
        log.error("Error with Excluded dicos server : " + str(e))
        return False

def get_entry(url,word,lang):
    try:
        response = requests.post(url + "/check_entry", data={"lang":lang,"word":word})
        log.info(word +" : "+ lang +" : "+ str(response.json()))
        if response.raise_for_status(): # bad response
            log.exception(response.raise_for_status())
            return False
        elif response.json()['exists']:
            return True
        else:
            return False
    except Exception as e:
        log.exception("Error with Excluded dicos analysis : " + str(e))
        return False
        
   
if __name__ == "__main__":
    url = 'http://127.0.0.1:5056'
    res = check_server(url)
    if res is False:
        print("Server not available. Please check lib/treetagger_server.py <lang> is running. Exiting.")
        exit()
    else:
        print("server available")
    res = check_lang(url,'fr')
    if res:
        print("Excluded dictionary available for lang 'fr'")
    else:
        print("Error with check_lang")

    res = get_entry(url, unidecode("present"),"fr")
    if res:
        print(res)
    else:
        print("Error with check_entry")

    res = get_entry(url, unidecode("arrivait"), "fr")
    if res:
        print(res)
    else:
        print("Error with check_entry")

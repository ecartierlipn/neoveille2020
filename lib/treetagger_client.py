import requests,logging

log = logging.getLogger(__name__)

def check_server(url):
    '''Function to check treetagger server available'''
    try:
        response = requests.get(url + '/check')
        log.info(response.json())
        if response.raise_for_status(): # bad response
            log.error(response.raise_for_status())
            return False
        else:
            return True
    except Exception as e:
        log.error("Error with Treetagger server : " + str(e))
        return False

def check_lang(url,lang):
    '''Function to check treetagger server lang'''
    try:
        response = requests.post(url + '/langcheck', data={'lang':lang})
        log.info(response.json())
        if response.raise_for_status(): # bad response
            log.error(response.raise_for_status())
            return False
        else:
            return True
    except Exception as e:
        log.error("Error with Treetagger server : " + str(e))
        return False

def get_nlp(url,text):
    try:
        response = requests.post(url + "/parse/", data={"text":text})
        log.info(response)
        if response.raise_for_status(): # bad response
            log.error(response.raise_for_status())
            return False
        else:
            return response.json()
    except Exception as e:
        log.error("Error with Treetagger analysis : " + str(e))
        return False
        
def get_nlp_and_unk(url,text):
    try:
        response = requests.post(url + "/parse_unk/", data={"text":text})
        log.info(response)
        if response.raise_for_status(): # bad response
            log.error(response.raise_for_status())
            return False
        else:
            return response.json()
    except Exception as e:
        log.error("Error with Treetagger analysis : " + str(e))
        return False

def get_unk(url,text):
    try:
        response = requests.post(url + "/get_unknown/", data={"text":text})
        log.info(response)
        if response.raise_for_status(): # bad response
            log.error(response.raise_for_status())
            return False
        else:
            return response.json()
    except Exception as e:
        log.error("Error with Treetagger analysis : " + str(e))
        return False
   
if __name__ == "__main__":
    url = 'http://127.0.0.1:5055'
    res = check_server(url)
    if res is False:
        print("Server not available. Please check lib/treetagger_server.py <lang> is running. Exiting.")
        exit()
    res = check_lang(url,'fr')
    if res:
        print(res)
    else:
        print("Error with check_lang")

    res = get_nlp(url, "Les macronisations microcosmicales fjqsdjfjj ffsqdqqd du candidat à la présidentielle fatiguent les antimacronistes.")
    if res:
        print(res)

    res = get_nlp_and_unk(url, "Les macronisations microcosmicales fjqsdjfjj ffsqdqqd du candidat à la présidentielle fatiguent les antimacronistes.")
    if res:
        print(res)

    res = get_unk(url, "Les macronisations microcosmicales fjqsdjfjj ffsqdqqd du candidat à la présidentielle fatiguent les antimacronistes.")
    if res:
        print(res)

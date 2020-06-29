# https://github.com/hunspell/hunspell
# dictionaries : look at https://extensions.openoffice.org/ or https://addons.mozilla.org/en-US/firefox/language-tools/
# The dictionaries are distributed as zip files typically with *.xpi or *.oxt extensions. 
# After downloading the desirable language file, rename it to a *.zip file.
# Each downloaded dictionary archive contains two text files with the *.aff and *.dic extensions and the name that (usually) 
# represents the corresponding language ISO codes, e.g. en-US.aff and en-US.dic (English US).
# Put the dictionaries in whatever directory and point to it in the global variable
# alternative to the present code can be to download the hunspell Python binding (pyhunspell), but seems less fine-tuned

import subprocess
import re
import logging
log = logging.getLogger(__name__)
import editdistance

# global variables : hunspell dictionaries
hunspell_dico={}
hunspell_dico['br']='/opt/nlp_tools/dictionaries/pt_BR/pt_BR'
hunspell_dico['fr']='/Users/emmanuelcartier/Desktop/GitHub/neoveille/neoveille-dev/resources/hunspell/hunspell-dicos/france/fr_FR'
hunspell_dico['zh']='/opt/nlp_tools/dictionaries/cz_CZ/cz_CZ'
hunspell_dico['pl']='/opt/nlp_tools/dictionaries/pl_PL/pl_PL'
hunspell_dico['ru']='/opt/nlp_tools/dictionaries/ru_RU/ru_RU'
hunspell_dico['gr']='/opt/nlp_tools/dictionaries/el_GR/el_GR'
hunspell_dico['cs']='/opt/nlp_tools/dictionaries/cs_CS/cs_CS'
hunspell_dico['en']='/Users/emmanuelcartier/Desktop/GitHub/neoveille/neoveille-dev/resources/hunspell/hunspell-dicos/anglais/en_US'
hunspell_dico['nl']='/Users/emmanuelcartier/Desktop/GitHub/neoveille/neoveille-dev/resources/hunspell/hunspell-dicos/pays-bas/nl_NL'



def hunspell_get_misspelled_from_text(s,lang="fr_FR"):
        ''' This function just return the list of misspelled words from input text
        '''
        cmd = 'echo "' + s + '" | hunspell -l -i UTF-8 --check-apostrophe -d ' + lang
        log.info("Input : " + s + "\n")
        try:
                p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                result, err = p.communicate()
                p.wait()
                if result:
                        return re.split("\n", result.decode("utf-8"))[:-1]

                else:
                        log.warning(str(err) + "\n")
                        return False
        except subprocess.CalledProcessError as e: # to be done : catch the actual error
                log.warning(str(e) + "\n")
                return False


def hunspell_check_text(s,lang="fr_FR",output="unknown"):
        ''' This function deals with a text and return the candidate neologisms. 
        Can be used as the main program to detect neologisms'''
        '''
        spell checking of text through hunspell
        echo 'commenc exist' | hunspell -d /Users/emmanuelcartier/prog-neoveille/dicos/hunspell_FR_fr-v5/fr_FR
        OK:    *
        Root:  + <root>
        Compound: -
        Miss:  & <original> <count> <offset>: <miss>, <miss>, ...
        None:  # <original> <offset>
        examples:
        Hunspell 1.3.3
        + commencer
        & commencear 3 0: commencera, commencer, commencement
        '''
        cmd = 'echo "' + s + '" | hunspell -i UTF-8 --check-apostrophe -d ' + lang
        log.info("Input : " + s + "\n")
        try:
                p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                result, err = p.communicate()
                p.wait()
                if result:
                        print(result.decode("utf-8"))
                        lines = re.split("\n", result.decode("utf-8"))
                        res = {}
                        for l2 in lines[1:-2]:
                                l = l2.rstrip()
                                if l[0] in ('*','+') and re.search(r"-",s):
                                        log.info("Compound word : " + l + "\n")
                                        res[l]="Hunspell : compound word"
                                        #res.append((l[2:],"Compound word"))
                                elif l[0] in ('*','+'):
                                        log.info("Simple word : " + l + "\n")
                                        #res.append((l[2:],"Existing word"))
                                elif l[0] in ('#'):
                                        log.info("Unknwon word, no suggestion : " + l + "\n")
                                        res[l[2:]]="Hunspell : no suggestion"
                                        #res.append((l[2:],"No suggestion"))
                                elif l[0] == '&':
                                        m = re.search(r"^& (.+?) ([0-9]+) [0-9]+: (.+)$", l,re.UNICODE)
                                        if (m):
                                                log.info("Number of suggestions :" + m.group(2)+ "\n")
                                                sugg = re.split(r", ", m.group(3))
                                                dist = editdistance.eval(m.group(1),sugg[0])
                                                print (str(dist),m.group(1),sugg[0])
                                                if dist<2:
                                                        log.info(m.group(1) + "Possible typo with : "+sugg[0])
                                                        res[m.group(1)]= "Hunspell : possible typo with : "+m.group(3)
                                                        #res.append((m.group(1),"Possible typo with : "+sugg[0]))
                                                else:
                                                        res[m.group(1)]= "Hunspell : (distance > 2) - possible typo with : "+m.group(3)                                                        
                                                        #res.append((m.group(1),"Neologism"))
                                        else:
                                                res[l]="Hunspell : no suggestion"                                                
                                                #res.append((l,"Neologism"))                                                
                        return (result,res)# finally return results

                else:
                        log.warning(str(err) + "\n")
                        return (False,False)
        except subprocess.CalledProcessError as e: # to be done : catch the actual error
                log.warning(str(e) + "\n")
                return (False,False)


def hunspell_check_word(s,lang):
        '''
        spell checking of word through hunspell
        echo 'commenc exist' | hunspell -d /Users/emmanuelcartier/prog-neoveille/dicos/hunspell_FR_fr-v5/fr_FR
        OK:    *
        Root:  + <root>
        Compound: -
        Miss:  & <original> <count> <offset>: <miss>, <miss>, ...
        None:  # <original> <offset>
        examples:
        Hunspell 1.3.3
        + commencer
        & commencear 3 0: commencera, commencer, commencement
        '''
        cmd = "echo '" + s + "' | hunspell -i UTF-8 --check-apostrophe -d " + lang
        log.info("Input : " + s + "\n")
        try:
                p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                result, err = p.communicate()
                p.wait()
                if result:
                        log.info(result.decode("utf-8"))
                        lines = re.split("\n", result.decode("utf-8"))
                        for l2 in lines[1:-2]:
                                l = l2.rstrip()
                                if l[0] in ('+'):
                                        log.info("affixation : " + l + "\n")
                                        return (True, u'affix - '+ l)
                                if l[0] in ('-'):
                                        log.info("Compound word : " + l + "\n")
                                        return (True, u'compound - '+ l)
                                elif l[0] in ('*'):
                                        log.info("Simple word : " + l + "\n")
                                        return (False, u'existing unit - '+ l)
                                elif l[0] in ('#'):
                                        log.info("Unknwon word, no suggestion : " + l + "\n")
                                        return (True,'unknownspellcheck')
                                elif l[0] == '&':
                                        #print "Hunspell results : " + l2
                                        m = re.search(r"^& ([^\s]+(?:-[^\s]+){0,4}) ([0-9]+) [0-9]+: (.+)$", l,re.UNICODE)
                                        if (m):
                                                log.info("Number of suggestions for "+ m.group(1) + " : " + m.group(2)+ "\n")
                                                sugg = re.split(r", ", m.group(3))
                                                dist = editdistance.eval(m.group(1),sugg[0])
                                                log.info(str(dist))
                                                if dist<2:
                                                        log.info("False : suggestion:2-:"+sugg[0]+ ":" + str(dist) )
                                                        return (False, "suggestion:2-:"+sugg[0]+ ":" + str(dist))
                                                else:
                                                        log.info("True : suggestion:2+:"+sugg[0]+ ":" + str(dist) )
                                                        return (True, "suggestion:2+:"+sugg[0]+ ":" + str(dist))
                                        else:
                                                return(True,"suggestion:"+l2)

                else:
                        log.warning(str(err) + "\n")
                        return (False, 'err')
        except subprocess.CalledProcessError as e: # to be done : catch the actual error
                log.warning(str(e) + "\n")
                return (False,'err')





if __name__ == "__main__":
        FORMAT = "%(levelname)s:%(asctime)s:%(message)s[%(filename)s:%(lineno)s - %(funcName)s()]"
        logging.basicConfig(format=FORMAT, datefmt='%m/%d/%Y %I:%M:%S %p', filename="./hunspell.log", filemode='w', level=logging.INFO)
        log = logging.getLogger(__name__)
        #sentence = "tot, c\'est-à-dire cet après-midi, est adminstraté jusqu\'aux bout djfkq fjsf à la maison"
        #print(hunspell_get_misspelled_from_text(sentence, hunspell_dico["fr"]))
        #print("*"*50)
       

        
       # (res,info)=hunspell_check_word("macronisait", hunspell_dico["fr"])
       # log.info(str(res) +"," + info + "\n")
       # print(res , info)
       # print("*"*50)
        sentence = "Mexique : un hacker affirme avoir faussé la présidentielle de 2012 Les révélations du hacker politique colombien Andres Sepulveda font l'effet d'une bombe depuis quelques heures au Mexique. En toute urgence, le gouvernement du président mexicain Enrique Peña Nieto a démenti...  Mexique : un hacker affirme avoir faussé la présidentielle de 2012 réagirLe hacker Andres Sepulveda dit avoir espionné les rivaux de l'actuel président mexicain Enrique Peña Nieto lors de la présidentielle 2012. Capture d'écran Twitter Les révélations du hacker politique colombien Andres Sepulveda font l'effet d'une bombe depuis quelques heures au Mexique. En toute urgence, le gouvernement du président mexicain Enrique Peña Nieto a démenti jeudi soir avoir recruté qui que ce soit pour espionner ses rivaux lors de la campagne présidentielle de 2012, comme l'affirme le hacker cité par l'agence de presse américaine Bloomberg. Andres Sepulved est incarcéré depuis 2014 pour avoir mené des actions d'espionnage visant à nuire au dialogue de paix entre le gouvernement colombien et la guerilla des FARC. Dans ses confessions à Bloomberg, il explique avoir travaillé durant des années sous les ordres d'un consultant vénézuélien, Juan José Rendon, pour mener campagne en faveur de différents partis politiques conservateurs dans plusieurs pays d'Amérique latine, dont le Mexique. Selon lui, l'entreprise de Rendon a touché, pendant la campagne présidentielle de 2012, 600.000 dollars du Parti révolutionnaire institutionnel (PRI) de Peña Nieto pour diffuser de fausses rumeurs sur Twitter et espionner les téléphones et le courrier des candidats de l'opposition Manuel Lopez Obrador et Josefina Vazquez Mota, ainsi que leur staff de campagne. Le PRI a finalement emporté l'élection après 12 années dans l'opposition. Selon Bloomberg, la carrière du hacker a commencé en 2005 avec le piratage de sites web de différents candidats à des élections, le vol de données et d'informations. Au fil des années, une véritable équipe de hacker a été constituée pour ce genre d'espionnage et leurs services étaient monnayés au prix fort. Andres Sepulveda indique à Bloomberg avoir mené également des campagnes sales pour des partis conservateurs lors des élections présidentielles de nombreux pays d'Amérique latine : Nicaragua, Panama, Honduras, Salvador, Colombie, Costa Rica, Guatemala et Venezuela. Si toutes les opérations du hacker n'ont pas toutes été synonymes de victoires pour les clients, Andres Sepulveda met en avant un grand nombre de succès et se targue d'avoir changé la face politique de l'Amérique Latine moderne : Mon travail consistait à rendre public les actions sales des candidats, à mener des opérations psychologiques, de la propagande noire, à lancer des rumeurs, finalement, tout le côté sombre de la politique que personne n'imagine. Une enquête réclamée Le gouvernement mexicain a immédiatement réagi, niant l'existence d'une quelconque relation entre l'équipe de la campagne présidentielle de 2012 et Andres Sepulveda, ainsi qu'avoir fait appel au consultant J.J. Rendon, a déclaré la présidence dans un communiqué. Nous rejetons également l'usage de l'information et la méthodologie décrites dans l'article, ajoute la présidence assurant que la campagne du PRI a été menée par les dirigeants, militants et sympathisants du parti. A la suite des accusations parues dans Bloomberg, l'ex-candidat à la présidentielle Lopez Obrador, du Parti de la révolution démocratique (PRD, gauche), a indiqué sur son compte Facebook être convaincu d'avoir été espionné durant la campagne de 2012 ainsi que celle de 2006. De son côté, Jesus Zambrano, président de la chambre des députés et dirigeant du PRD, a demandé que ces accusations fassent l'objet d'une enquête de la part des autorités judiciaires mexicaines. Les révélations du hacker politique colombien Andres Sepulveda font l'effet d'une bombe depuis quelques heures au Mexique. En toute urgence, le gouvernement du président mexicain Enrique Peña Nieto a démenti jeudi soir avoir recruté qui que ce..."
        (res,info)=hunspell_check_text(sentence, hunspell_dico["fr"]) #
        log.info(str(res) +"," + str(info) + "\n")
        print("*"*50)
        print(res)
        print("*"*50)
        print(info)

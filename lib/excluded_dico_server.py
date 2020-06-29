# A simple web server for Excluded dicos

from flask import Flask, request,jsonify
import mysql.connector
from mysql.connector import Error
import sys
from unidecode import unidecode

# mysql credentials
user='root'
password='root'
host='localhost'
db_dico='datatables'

# language parameters
available_langs = ('fr','it','pl','cz')
# main access to all dicos
dicos={}

app = Flask(__name__)

# exclusion dictionary loading from db  
def load_exclusion_dico(lang):
    '''
        Connect to MySQL database and return a dictionary with all the excluded forms as keys from all dictionaries 
        for this language lang
        Parameters
        ----------
        lang : TYPE str
        the language two-letters iso_code
        Returns
        -------
        exclusion_dico : TYPE dict
        the exclusion dictionary
    '''
    print("Loading dico for language : " + lang)
    dict_exclusion={}
    try:
        conn = mysql.connector.connect(host=host,
                                       database=db_dico,
                                       user=user,
                                       password=password)
        if conn.is_connected():
            #log.info('Connected to Mysql database' + "\n")
            cursor = conn.cursor()
            args = [lang]
            cursor.callproc('get_dicos_generic', args)
            for result in cursor.stored_results():
                for row in result.fetchall():
                    #print(row[0],unidecode(row[0]))
                    if row[0]:
                        dict_exclusion[unidecode(row[0].strip())]=1
            cursor.close()
            conn.close()
            print("Exclusion dico loaded : " + str(len(dict_exclusion)) + " entries.")
            return dict_exclusion
    except Exception as e:
        print("Problem while loading exclusion dictionary. Error details : " + str(e))
        return False

    except Error as e:
        print(str(e))
        return False
                    

if len(sys.argv) < 2:
    print("You must give the language iso_code for which to load excluded dicos (fr,en,de,es,pt,it,nl,xx). Exiting.")
    exit()
else:
    # load excluded dico for each language given
    langs = sys.argv[1:]
    try :
        for lang in langs:
            excluded_dico = load_exclusion_dico(lang)
            dicos[lang]=excluded_dico
    except Exception as e:
        print("Bad iso code or other error : ", str(e))
        exit()

@app.route("/check")
def check():
    "check server is running"
    return jsonify("True")

@app.route("/check_entry", methods=['GET','POST'])
def check_entry():
    "check if word exists in the lang dictionary"
    lang = request.form['lang']
    word = request.form['word']
    if lang in dicos.keys():
        if word in dicos[lang].keys():
            print(word + ": exists")
            print(lang,word, " exists")
            return jsonify({'exists': True})
        else :
            print(lang,word, "  does not exist")
            return jsonify({'exists': False})
    else:
        return jsonify({'exists': True})

@app.route("/check_lang", methods=['GET','POST'])
def check_lang():
    "check if lang has an excluded dictionary loaded"
    lang = request.form['lang']
    print(lang)
    if lang in dicos.keys():
        return jsonify("True")
    else:
        return jsonify("False")


if __name__ == "__main__":
    app.run(debug=True, port=5056)
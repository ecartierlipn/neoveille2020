# A simple web server for treetagger
# doc : https://treetaggerwrapper.readthedocs.io/en/latest

from flask import Flask, request,jsonify
import treetaggerwrapper,re,os,sys
import pprint   # For proper print of sequences.

# treetagger root path
# first you need to install treetagger (programs and per language models)
taggerdir = '/Users/emmanuelcartier/treetagger' # change to your treetagger installation path
# correspondance file from Treetagger ¨POS tags to CONLL Universal Tags
tags_convert='../ling_resources/treetagger_conll/'

lang=''
def tag_convert(filename):
    '''
    Function to load a tagset conversion dict (from treetagger tagset to conll-u tagsets. Depends on language, 
    thus requiring a language-dependent processing.

    Parameters
    ----------
    filename : TYPE str
    the complete path to the file (format TREETAGGER TAG tab CONLL-U tag tab description)

    Returns
    -------
    tagset_dict : TYPE dict
    the tagset dictionary (key : treetagger tag, value : conll-u tag)
    '''
    tagset_dict={}
    try:
        with open(filename, mode="r", encoding="utf-8") as fin:
            for line in fin:
                data = line.strip().split("\t")
                if len(data)== 3:
                    tagset_dict[data[0]]= data[1]
        return tagset_dict
    except Exception as e:
        print("Error loading tagset conversion file. File : " + filename + ". Error : " + str(e))
        return False
                    
if len(sys.argv) != 2:
    print("You must give the iso_code of the language model to launch (fr,en,de,es,pt,it,nl,xx). Exiting.")
    exit()
else:
    # load treetagger object wrapper with lang parameter
    lang = sys.argv[1] # CHANGE ACCORDING TO THE LANGUAGE YOU WORK ON !
    try :
        tagger = treetaggerwrapper.TreeTagger(TAGLANG=lang, TAGDIR=taggerdir, TAGOPT="-token -lemma -sgml")
        tagset_dict = tag_convert(tags_convert + lang + "_tagset.txt")
        if tagset_dict is False:
            exit()
        else:
            print("Tagset Loaded :" + str(tagset_dict))
        app = Flask(__name__)
        print('Treetagger ready for language : ' + lang)
    except Exception as e:
        print("Bad iso code or other error : ", str(e))
        exit()

@app.route("/check")
def check():
    return jsonify("True")

@app.route("/langcheck", methods=['GET','POST'])
def langcheck():
    wlang = request.form['lang']
    print(lang,wlang)
    if wlang == lang:
        return jsonify("True")
    else:
        return jsonify("False")

@app.route("/parse/", methods=['POST'])
def parse_text():
    try:
        text = request.form['text']
        tags = tagger.tag_text(text)
        pprint.pprint(tags)
        tagsconvert = []
        for wordinfo in tags:
            worddata = wordinfo.split('\t')
            wordconvert = worddata[0] + "\t" + tagset_dict.get(worddata[1],worddata[1]) + "\t" + worddata[2]
            tagsconvert.append(wordconvert)
        return jsonify(tagsconvert)
    except Exception as e:
        print("Problem with tagging text : ", text, ", message : ", str(e) )
        exit()

@app.route("/parse_unk/", methods=['POST'])
def parse_text_unk():
    try:
        text = request.form['text']
        tags = tagger.tag_text(text)
        #tags2 = treetaggerwrapper.make_tags(tags, allow_extra=True) #, allow_extra=True
        unk = {}
        tagsconvert = []
        for wordinfo in tags:
            worddata = wordinfo.split('\t')
            wordconvert = worddata[0] + "\t" + tagset_dict.get(worddata[1],worddata[1]) + "\t" + worddata[2]
            tagsconvert.append(wordconvert)
            if re.search(r"<unknown>", wordconvert, re.I):
                unk[wordinfo] = unk.get(wordconvert,0)+1
        pprint.pprint(tags)
        pprint.pprint(tagsconvert)
        #pprint.pprint(tags2)
        return jsonify({'taggedtext':tagsconvert,'unknown':unk})
    except Exception as e:
        print("Problem with tagging text : ", text, ", message : ", str(e) )
        exit()


@app.route("/get_unknown/", methods=['POST'])
def get_unknown():
    try:
        text = request.form['text']
        tags = tagger.tag_text(text)
        unk = {}
        tagsconvert = []
        for wordinfo in tags:
            worddata = wordinfo.split('\t')
            wordconvert = worddata[0] + "\t" + tagset_dict.get(worddata[1],worddata[1]) + "\t" + worddata[2]
            tagsconvert.append(wordconvert)
            if re.search(r"<unknown>", wordconvert, re.I):
                unk[wordinfo] = unk.get(wordconvert,0)+1
        #pprint.pprint(tags2)
        return jsonify(unk)
    except Exception as e:
        print("Problem with tagging text : ", text, ", message : ", str(e) )
        exit()


if __name__ == "__main__":
    app.run(debug=True, port=5055)
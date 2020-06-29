import treetaggerwrapper as ttpw
tagger = ttpw.TreeTagger(TAGLANG='fr', TAGOPT="-prob -threshold 0.7 -token -lemma -sgml")
tags = tagger.tag_text('Voici un petit test de TreeTagger pour voir.')
import pprint
pprint.pprint(tags)
tags2 = ttpw.make_tags(tags, allow_extra=True)
pprint.pprint(tags2)
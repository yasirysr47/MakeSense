import nltk
from collections import defaultdict
import os, sys
#depended upon scrapy and genie and data_store
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from genie.genie import Genie
from DataStore.dir import Dir
import DataStore.src as src

MAX_NUMBER_SUBTITLES = 7
PATH = Dir()

class Sense():
    def __init__(self,data=''):
        self.big_data = data
        self.pos_title_dict = defaultdict(lambda: 0)

    def make_possible_subtitles(self, data):
        sent_list = nltk.sent_tokenize(data)
        for sent in sent_list:
            pos_ti = sent.split('\n\n')
            for each_pos in pos_ti:
                if each_pos in self.pos_title_dict:
                    self.pos_title_dict[each_pos] += 1
                else:
                    self.pos_title_dict[each_pos] = 1
        
    def get_possible_subtitles(self):
        pos_title_list = sorted(self.pos_title_dict.items(), key=lambda k: (k[1],k[0]), reverse=True)
        return_list = []
        #top_count = pos_title_list[0][1]
        #top = 0

        for ti, _ in pos_title_list[: MAX_NUMBER_SUBTITLES]:
            return_list.append(ti)
        '''
        # logic to consider all top scored entity as sub titles
        for each_ti, count in pos_title_list:
            if count == top_count:
                return_list.append(each_ti)
            elif len(return_list) < MAX_NUMBER_SUBTITLES 
            and len(pos_title_list) > MAX_NUMBER_SUBTITLES 
            and top < MAX_NUMBER_SUBTITLES:
                for ti, sc in pos_title_list[top : MAX_NUMBER_SUBTITLES]:
                    return_list.append(ti)
            top += 1
        '''
        return ", ".join(return_list)

    def save_subtitle_list(self, src_filename, subtitle_filename):
        url_list = []
        url = 'placeholder'
        fp = open(src_filename, "r")
        while(url):
            line = fp.readline().strip()
            url = line
            try:
                genie = Genie(url, pattern=r'(\[\s*[\s\w]+\s*\])', mode='r')
            except:
                #might be timeout failures
                url_list.append(url)

            data = genie.get_data()
            self.make_possible_subtitles(data)
            if not url:
                fp.close()
                break
        '''
        # handle failed URL's        
        for url in url_list:
            genie = Genie(url, pattern=r'(\[\s*[\s\w]+\s*\])', mode='r')
            data = genie.get_data()
            sense.make_possible_subtitles(data)
        '''

        with open(subtitle_filename, "w+") as tp:
            tp.write(sense.get_possible_subtitles())



if __name__ == "__main__":
    src_filename = src.src_filename
    trg_filename = src.trg_filename
    #trg_filename = os.path.join(PATH.pro_data, trg_filename)
    sense = Sense()
    sense.save_subtitle_list(src_filename, trg_filename)
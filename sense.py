import nltk
from collections import defaultdict
import os, sys, re
from urllib.parse import urlsplit
import urllib.error as error
#depended upon scrapy and genie and data_store
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from genie.genie import Genie
from DataStore.dir import Dir
import DataStore.src as src
from scrapy.scrapy import Scraper

MAX_NUMBER_SUBTITLES = 15
PATH = Dir()

class Sense():
    def __init__(self,data=''):
        self.data = data.replace('\n\n', '.  ').replace('..','. ')
        self.pos_title_dict = defaultdict(lambda: 0)

    def make_possible_subtitles(self, data):
        '''
        stale function: not usable for generic purpose
        '''
        sent_list = nltk.sent_tokenize(data)
        for sent in sent_list:
            pos_ti = sent.split('\n\n')
            for each_pos in pos_ti:
                if each_pos in self.pos_title_dict:
                    self.pos_title_dict[each_pos] += 1
                else:
                    self.pos_title_dict[each_pos] = 1
        
    def get_possible_subtitles(self):
        '''
        stale function: not usable for generic purpose
        '''
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

    def get_sub_heading_titles(self):
        sub_file = open(PATH.sub_heading, "r")
        sub_headings = sub_file.readline().lower().replace(', ',',').split(',')
        sub_file.close()
        return sub_headings


    def get_sub_heading_data(self, data=''):
        '''
        function to get data under each sub headings.
        '''
        if not data:
            data = self.data
        data_block = {}
        sub_headings = src.symptom_cause_sub_headings
        cur_head = ''
        prev_head = ''
        sent_list = nltk.sent_tokenize(data)
        para_sent_list = []
        for sent in sent_list:
            sent = sent.strip('.')
            skip_flag = 0
            for bword in src.blacklist_words:
                if bword in sent:
                    skip_flag = 1
                    break
            if skip_flag:
                continue
            flag = 0
            if len(sent.split()) == 1 or sent in sub_headings:
                word = sent
                if word in sub_headings and word != cur_head:
                    prev_head = cur_head
                    flag = 1
                    cur_head = word 
            sent = sent.strip()
            if flag:
                if prev_head:
                    data_block[prev_head] = para_sent_list
                    para_sent_list = []
                sent = sent.replace(cur_head, '', 1).strip()
                
            if sent and sent not in para_sent_list:
                para_sent_list.append(sent)
            #print(para_sent_list)

        if cur_head != prev_head:
            data_block[cur_head] = para_sent_list

        return data_block

    def process_parse_data(self, data, sub_heading):
        main_heading = ''
        para_flag = 0
        final_data = ""
        skip_para = 0
        sub_headings = sub_heading
        for line in data.split('\n'):
            if line.startswith('<h1>'):
                main_heading = re.sub('<.*>', '', line)
                final_data = "{}{}\n".format(final_data, main_heading)
            if not main_heading:
                continue
            if line.startswith(("<h2>", "<h3>", "<p>")):
                new_line = re.sub('<.*>', '', line)
                if line.startswith("<p>") and new_line and not skip_para:
                    para_flag = 1
                else:
                    #comment it out when not needed; to get top sub headings
                    if line.startswith(("<h2>", "<h3>")):
                        self.pos_title_dict[new_line] = self.pos_title_dict.get(new_line, 0) + 1
                    para_flag = 0
                    if new_line.lower() not in sub_headings:
                        skip_para = 1
                        continue
                    if line.startswith(("<h2>", "<h3>")):
                        final_data = "{}{}\n".format(final_data, src.line_split)
                        para_flag = 1
                    skip_para = 0
                if new_line:
                    final_data = "{}{}\n".format(final_data, new_line)
            elif line.startswith(">>>"):
                if para_flag:
                    new_line = re.sub('>>>', '->', line)
                    if new_line:
                        final_data = "{}{}\n".format(final_data, new_line)

        return final_data

    def find_title(self, url):
        path = urlsplit(url)
        return path.path.split('/',4)[2]

        
    def generate_bigdata(self, key, sub_heading_list, file_loc):
        genie = Genie()
        file_name = src.bigdata_keys[key]
        loc = file_loc
        fp = open(file_name, "r+")
        url = fp.readline()
        while(url):
            scrap = Scraper(url)
            try:
                scrap_data = scrap.init_parser(url)
            except:
                #print(url)
                url = fp.readline()
                continue
            parse_data = genie.convert_parse_data(scrap_data)
            article = self.process_parse_data(parse_data, sub_heading_list)
            title = self.find_title(url)
            path = os.path.join(loc, "{}_{}.txt".format(title, key))
            genie.save_data(article, path)
            #print("=====  saved : {}_{}.txt  =====".format(title, key))
            url = fp.readline()
        fp.close()

    def start_generating_bigdata(self, key):
        sub_heading = None
        loc = None
        if key == 'symptom_cause':
            sub_heading = src.symptom_cause_sub_headings
            loc = PATH.disease_data_dir
        elif key == 'doctors_departments':
            sub_heading = src.doctors_departments_sub_headings
            loc = PATH.department_data_dir
        elif key == 'diagnosis_treatment':
            sub_heading = src.diagnosis_treatment_sub_headings
            loc = PATH.treatment_data_dir
        
        self.generate_bigdata(key, sub_heading, loc)

        

    def test_generate_bigdata(self, url, sub_heading):
        genie = Genie()
        scrap = Scraper(url)
        try:
            scrap_data = scrap.init_parser(url)
        except:
            print("url failed")
            return None
        parse_data = genie.convert_parse_data(scrap_data)
        genie.save_data(parse_data, 'fdata.txt')
        article = self.process_parse_data(parse_data, sub_heading)
        genie.save_data(article, 'article.txt')
        title = self.find_title(url)
        path = os.path.join('.', "{}_{}.txt".format(title, 'log'))
        genie.save_data(article, path)









if __name__ == "__main__":
    # src_filename = src.src_filename
    # trg_filename = src.trg_filename
    # url = 'https://www.mayoclinic.org/diseases-conditions/chickenpox/symptoms-causes/syc-20351282'
    # url = 'https://www.mayoclinic.org/diseases-conditions/common-cold/symptoms-causes/syc-20351605'
    # url1 = 'https://www.mayoclinic.org/diseases-conditions/chickenpox/diagnosis-treatment/drc-20351287'
    url = 'https://www.mayoclinic.org/diseases-conditions/hemorrhoids/doctors-departments/ddc-20360281'
    #genie = Genie(url, pattern=src.clean_data_pattern[2], mode='r')
    import time
    start_time = time.time()
    genie = Genie()
    sense = Sense()
    #sense.generate_symptom_cause_bigdata()
    # sh = src.doctors_departments_sub_headings
    # sense.test_generate_bigdata(url, sh)

    # sense = Sense()   
    # sense.start_generating_bigdata("doctors_departments")
    # genie.save_data(sense.get_possible_subtitles(), "doctors_departments_subheading.txt")
    

    key_dict = {
        "diagnosis_treatment" : "diagnosis_treatment_subheading.txt",
        "symptom_cause" : "symptom_cause_subheading.txt",
        "doctors_departments" : "doctors_departments_subheading.txt"
    }
    # key_dict = {}
    for key, fname in key_dict.items():
        sense = Sense()
        sense.start_generating_bigdata(key)
        genie.save_data(sense.get_possible_subtitles(), fname)
    
    end_time = time.time()
    print("Total time taken : {} s".format(end_time-start_time))

    

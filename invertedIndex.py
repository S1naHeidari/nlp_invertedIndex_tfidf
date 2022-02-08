import hashedindex
import os
import re
import datetime
from nltk.stem.porter import PorterStemmer
import xml.etree.ElementTree as ET
myPath = "/home/raycatcher/Desktop/IR_InvertedIndex/Cars"
start = datetime.datetime.now()
def xml_to_ii(myPath = "/home/raycatcher/Desktop/IR_InvertedIndex/Cars"):
    documents = {}
    documentId=1
    file_count = 0
    year_count = {2007:0,2008:0,2009:0}
    p = re.compile('<text>.*</text>',re.IGNORECASE)
    p2 = re.compile('<favorite>.*</favorite>',re.IGNORECASE)
    for (dirpath, dirnames, filenames) in os.walk(myPath):
        file_count+=len(filenames)
        for chosen_file in filenames:
            my_file = open(dirpath+'/'+chosen_file,'r',encoding='windows-1252')
            my_file = my_file.read()
            all_documents1 = p.findall(my_file.lower())
            all_documents2 = p2.findall(my_file.lower())
            for i in range(len(all_documents1)-1):
                all_documents1[i] = all_documents1[i].replace('<text>','')
                all_documents1[i] = all_documents1[i].replace('</text>','')
                all_documents2[i] = all_documents2[i].replace('<favorite>','')
                all_documents2[i] = all_documents2[i].replace('</favorite>','')
            if chosen_file.split('_')[0] == '2007':
                year_count[2007]+=len(all_documents1)
            if chosen_file.split('_')[0] == '2008':
                year_count[2008]+=len(all_documents1)
            if chosen_file.split('_')[0] == '2009':
                year_count[2009]+=len(all_documents1)
            why = chosen_file

            for i in range(len(all_documents1)-1):
                whole = all_documents1[i]+all_documents2[i]
                documents[documentId] = {"text":whole,"file_name":chosen_file}
                documentId+=1
    return documents, year_count

def preprocessing(documents):
    tokenizing = [re.findall('\w+',documents[documentId]["text"]) for documentId in documents]

    token_length = 0
    for doc in tokenizing:
        token_length+=len(doc)
    print(f'Number of tokens before preprocessing: {token_length}')

    stop_words = open("/home/raycatcher/Desktop/IR_InvertedIndex/stopwords.txt",'r',encoding='windows-1252')
    stop_words = stop_words.read()
    stop_words = stop_words.split()
    stopWords_removed = []
    stems = []
    finished_dic = {} 
    for doc in tokenizing:
        doc = [d for d in doc if d not in stop_words]
        stopWords_removed.append(doc)
    
    stopWord_length = 0
    for doc in stopWords_removed:
        stopWord_length += len(doc)
    print(f'Number of tokens after removing stop words: {stopWord_length}')

    porter = PorterStemmer()
    for doc in stopWords_removed:
        doc = [porter.stem(s) for s in doc]
        stems.append(doc)
    
    stem_length = 0
    for doc in stems:
        stem_length+=len(doc)
    print(f'Number of tokens after stemming: {stem_length}')

    for documentId in documents:
        finished_dic[documentId] = {"text":' '.join(stems[documentId-1]),"file_name":documents[documentId]["file_name"]}

    return finished_dic

def create_index(documents):
    inverted_index={}
    word_count={}
    for documentId, text in documents.items():
        for word in text["text"].lower().split():
            word_count[word] = word_count.get(word,0)+1
            if inverted_index.get(word,False):
                if documentId not in inverted_index[word]:
                    inverted_index[word].append(documentId)
            else:
                    inverted_index[word] = [documentId]
    return inverted_index, word_count


documents, years_count = xml_to_ii(myPath)
preprocessed = preprocessing(documents)
doc_count = len(preprocessed)
print(f'Number of preprocessed documents: {doc_count}')
cars = []
for file_name in range(1,len(preprocessed)-1):
    cars.append(preprocessed[file_name]["file_name"])

distinct_cars = []
for car in cars:
    if car.split('_')[1] not in distinct_cars:
        distinct_cars.append(car.split('_')[1])

print(f'Number of distinct cars: {len(distinct_cars)} {distinct_cars}')
year_count = {}
for docId in preprocessed:
    if preprocessed[docId]["file_name"].split('_')[0]=='2007':
        if 2007 in year_count:
            year_count[2007]+=1
        else:
            year_count[2007]=1
    if preprocessed[docId]["file_name"].split('_')[0]=='2008':
        if 2008 in year_count:
            year_count[2008]+=1
        else:
            year_count[2008]=1
    if preprocessed[docId]["file_name"].split('_')[0]=='2009':
        if 2009 in year_count:
            year_count[2009]+=1
        else: 
            year_count[2009]=1


print(f'Number of cars for every year: {year_count}')
print(f'Number of documents for every year: {years_count}')
tf, df = create_index(preprocessed)
print(tf)
finish = datetime.datetime.now()
print(finish-start)


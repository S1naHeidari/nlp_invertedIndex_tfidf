#!/usr/bin/env python
import json
import math
import os
import re
import sys
import pickle

from PorterStemmer import PorterStemmer


class IRSystem:

    def __init__(self):
        # For holding the data - initialized in read_data()
        self.titles = []
        self.docs = []
        self.vocab = []
        # For the text pre-processing.
        self.alphanum = re.compile('[^a-zA-Z0-9]')
        self.p = PorterStemmer()


    def get_uniq_words(self):
        uniq = set()
        for doc in self.docs:
            for word in doc:
                uniq.add(word)
        return uniq


    def __read_raw_data(self, dirname):
        print("Stemming Documents...")

        titles = []
        docs = []
        os.mkdir('%s/stemmed' % dirname)
        title_pattern = re.compile('(.*) \d+\.txt')

        # make sure we're only getting the files we actually want
        filenames = []
        for filename in os.listdir('%s/raw' % dirname):
            if filename.endswith(".txt") and not filename.startswith("."):
                filenames.append(filename)

        for i, filename in enumerate(filenames):
            title = title_pattern.search(filename).group(1)
            print("    Doc %d of %d: %s" % (i+1, len(filenames), title))
            titles.append(title)
            contents = []
            f = open('%s/raw/%s' % (dirname, filename), 'r')
            of = open('%s/stemmed/%s.txt' % (dirname, title), 'w')
            for line in f:
                # make sure everything is lower case
                line = line.lower()
                # split on whitespace
                line = [xx.strip() for xx in line.split()]
                # remove non alphanumeric characters
                line = [self.alphanum.sub('', xx) for xx in line]
                # remove any words that are now empty
                line = [xx for xx in line if xx != '']
                # stem words
                line = [self.p.stem(xx) for xx in line]
                # add to the document's conents
                contents.extend(line)
                if len(line) > 0:
                    of.write(" ".join(line))
                    of.write('\n')
            f.close()
            of.close()
            docs.append(contents)
        return titles, docs


    def __read_stemmed_data(self, dirname):
        print("Already stemmed!")
        titles = []
        docs = []

        # make sure we're only getting the files we actually want
        filenames = []
        for filename in os.listdir('%s/stemmed' % dirname):
            if filename.endswith(".txt") and not filename.startswith("."):
                filenames.append(filename)

        if len(filenames) != 60:
            msg = "There are not 60 documents in ../data/RiderHaggard/stemmed/\n"
            msg += "Remove ../data/RiderHaggard/stemmed/ directory and re-run."
            raise Exception(msg)

        for i, filename in enumerate(filenames):
            title = filename.split('.')[0]
            titles.append(title)
            contents = []
            f = open('%s/stemmed/%s' % (dirname, filename), 'r')
            for line in f:
                # split on whitespace
                line = [xx.strip() for xx in line.split()]
                # add to the document's conents
                contents.extend(line)
            f.close()
            docs.append(contents)

        return titles, docs


    def read_data(self, dirname):
        """
        Given the location of the 'data' directory, reads in the documents to
        be indexed.
        """
        # NOTE: We cache stemmed documents for speed
        #       (i.e. write to files in new 'stemmed/' dir).

        print("Reading in documents...")
        # if tfidf file exists, load it to self.tfidf
        filenames = os.listdir(dirname)
        subdirs = os.listdir(dirname)
        if 'stemmed' in subdirs:
            titles, docs = self.__read_stemmed_data(dirname)
        else:
            titles, docs = self.__read_raw_data(dirname)

        # Sort document alphabetically by title to ensure we have the proper
        # document indices when referring to them.
        ordering = [idx for idx, title in sorted(enumerate(titles),
            key = lambda xx : xx[1])]

        self.titles = []
        self.docs = []
        numdocs = len(docs)
        for d in range(numdocs):
            self.titles.append(titles[ordering[d]])
            self.docs.append(docs[ordering[d]])

        # Get the vocabulary.
        self.vocab = [xx for xx in self.get_uniq_words()]

    def compute_tfidf(self):

        print("Calculating tf-idf...")
        # Check if the tf.idf file exists
        if os.path.exists('tfidf'):
            with open('tfidf', 'rb') as f:
                self.tfidf = pickle.load(f)
            return None
        
        # Create tf.idf dictionary
        self.tfidf = {}
        # Create a dict for every word in tfidf, with keys corresponding to document IDs
        for word in self.vocab:
            for d in range(len(self.docs)):
                if word not in self.tfidf:
                    self.tfidf[word] = {}
                self.tfidf[word][d] = 0.0

        # For each word in tfidf dict
        for word in self.tfidf:
            # Compute inverse document frequency
            idf = len(self.inv_index[word])
            idf = math.log10(len(self.docs)/idf)
            # for each doc in posting list of the word
            for doc_index in self.inv_index[word]:
                if word in self.docs[doc_index]:
                    # multiply tf and idf
                    self.tfidf[word][doc_index] = (1 + math.log10(self.countX(self.docs[doc_index], word))) * idf

        # Dump tfidf dictionary in this folder using pickle
        with open('tfidf', 'wb') as f:
            pickle.dump(self.tfidf, f, protocol=pickle.HIGHEST_PROTOCOL)  

    # This function is used to count the instances of a word inside a list
    def countX(self, lst, x):
        count = 0
        for ele in lst:
            if (ele == x):
                count = count + 1
        return count
    
    def get_tfidf(self, word, document):
        # ------------------------------------------------------------------
        # TODO: Return the tf-idf weigthing for the given word (string) and
        #       document index.
        # tfidf = 0.0
        # if word in self.tfidf:
        #     tfidf = self.tfidf[word][document]
        # else:
        #     print('The word does not exist.')
        # # ------------------------------------------------------------------
        # return tfidf

        tfidf = 0.0
        # Just asigning tfidf value for the given word and document
        tfidf = self.tfidf[word][document]
        # ------------------------------------------------------------------
        return tfidf


    def get_tfidf_unstemmed(self, word, document):
        """
        This function gets the TF-IDF of an *unstemmed* word in a document.
        Stems the word and then calls get_tfidf. You should *not* need to
        change this interface, but it is necessary for submission.
        """
        word = self.p.stem(word)
        return self.get_tfidf(word, document)


    def index(self):
        """
        Build an index of the documents.
        """
        print("Indexing...")
        # ------------------------------------------------------------------
        
        # create a dict for inverted index
        inv_index = {}
        # assign an empty list to each word in the inverted index
        for word in self.vocab:
            inv_index[word] = []
        
        # for each doc
        for doc in self.docs:
            # for each word in doc
            for word in doc:
                if self.docs.index(doc) not in inv_index[word]:
                    # appending the doc to the word's posting list
                    inv_index[word].append(self.docs.index(doc))

        self.inv_index = inv_index

        # ------------------------------------------------------------------


    def get_posting(self, word):
        """
        Given a word, this returns the list of document indices (sorted) in
        which the word occurs.
        """
        # ------------------------------------------------------------------
        posting = []
        if word in self.inv_index:
            # Just assigning the posting list to posting variable
            posting = self.inv_index[word]
        return posting
        # ------------------------------------------------------------------


    def get_posting_unstemmed(self, word):
        """
        Given a word, this *stems* the word and then calls get_posting on the
        stemmed word to get its postings list. You should *not* need to change
        this function. It is needed for submission.
        """
        word = self.p.stem(word)
        return self.get_posting(word)


    def boolean_retrieve(self, query):
        """
        Given a query in the form of a list of *stemmed* words, this returns
        the list of documents in which *all* of those words occur (ie an AND
        query).
        Return an empty list if the query does not return any documents.
        """
        
        # using Python's set feature to find intersection of each word of the query's posting list and 
        intersection_set = set([i for i in range(len(self.docs))])
        for term in query:
            intersection_set = intersection_set & set(self.inv_index[term])
        
        docs = list(intersection_set)

        return sorted(docs)   # sorted doesn't actually matter


    def rank_retrieve(self, query):
        """
        Given a query (a list of words), return a rank-ordered list of
        documents (by ID) and score for the query.
        """

        scores = [0.0 for xx in range(len(self.docs))]

        # store term frequencies for the query
        query_tf = {}
        for word in query:
            if word not in query_tf:
                query_tf[word] = 1
            else:
                query_tf[word]+=1
        # compute log of term frequencies
        for word in query_tf:
            query_tf[word] = 1 + math.log10(query_tf[word])
        
        # for each word in the query
        for word in query:
            # for each doc of the word's posting list
            for doc in self.inv_index[word]:
                # multiply tf.idf value of document with term frequency of the word in the query
                scores[doc] += (self.tfidf[word][doc]) * query_tf[word]

        for d in range(len(scores)):
            length = 0
            # terms: words in the document
            terms =  set([w for w in self.docs[d]])
            # compute length of the document tf.idf vector
            length = 0
            for word in terms:
                length += pow(self.tfidf[word][d], 2)
            length = math.sqrt(length)
            # normalize the score
            scores[d] = scores[d] / length

        #create a list of tuples (docID, score)
        ranking = []
        for i in range(len(scores)):
            ranking.append((i, scores[i]))
        #sort the tuples based on score values
        ranking.sort(key = lambda x: x[1], reverse = True)
        #append top 10 cosine similarity scores to results variable
        results = []
        for i in range(10):
            results.append(ranking[i])
        
        return results


    def process_query(self, query_str):
        """
        Given a query string, process it and return the list of lowercase,
        alphanumeric, stemmed words in the string.
        """
        # make sure everything is lower case
        query = query_str.lower()
        # split on whitespace
        query = query.split()
        # remove non alphanumeric characters
        query = [self.alphanum.sub('', xx) for xx in query]
        # stem words
        query = [self.p.stem(xx) for xx in query]
        return query


    def query_retrieve(self, query_str):
        """
        Given a string, process and then return the list of matching documents
        found by boolean_retrieve().
        """
        query = self.process_query(query_str)
        return self.boolean_retrieve(query)


    def query_rank(self, query_str):
        """
        Given a string, process and then return the list of the top matching
        documents, rank-ordered.
        """
        query = self.process_query(query_str)
        return self.rank_retrieve(query)


def run_tests(irsys):
    print("===== Running tests =====")

    ff = open('../data/queries.txt')
    questions = [xx.strip() for xx in ff.readlines()]
    ff.close()
    ff = open('../data/solutions.txt')
    solutions = [xx.strip() for xx in ff.readlines()]
    ff.close()

    epsilon = 1e-4
    for part in range(4):
        points = 0
        num_correct = 0
        num_total = 0

        prob = questions[part]
        soln = json.loads(solutions[part])

        if part == 0:     # inverted index test
            print("Inverted Index Test")
            words = prob.split(", ")
            for i, word in enumerate(words):
                num_total += 1
                posting = irsys.get_posting_unstemmed(word)
                if set(posting) == set(soln[i]):
                    num_correct += 1

        elif part == 1:   # boolean retrieval test
            print("Boolean Retrieval Test")
            queries = prob.split(", ")
            for i, query in enumerate(queries):
                num_total += 1
                guess = irsys.query_retrieve(query)
                if set(guess) == set(soln[i]):
                    num_correct += 1

        elif part == 2:   # tfidf test
            print("TF-IDF Test")
            queries = prob.split("; ")
            queries = [xx.split(", ") for xx in queries]
            queries = [(xx[0], int(xx[1])) for xx in queries]
            for i, (word, doc) in enumerate(queries):
                num_total += 1
                guess = irsys.get_tfidf_unstemmed(word, doc)
                if guess >= float(soln[i]) - epsilon and \
                        guess <= float(soln[i]) + epsilon:
                    num_correct += 1

        elif part == 3:   # cosine similarity test
            #print("Cosine Similarity Test")
            queries = prob.split(", ")
            for i, query in enumerate(queries):
                num_total += 1
                ranked = irsys.query_rank(query)
                top_rank = ranked[0]
                if top_rank[0] == soln[i][0]:
                    if top_rank[1] >= float(soln[i][1]) - epsilon and \
                            top_rank[1] <= float(soln[i][1]) + epsilon:
                        num_correct += 1

        feedback = "%d/%d Correct. Accuracy: %f" % \
                (num_correct, num_total, float(num_correct)/num_total)
        if num_correct == num_total:
            points = 3
        elif num_correct > 0.75 * num_total:
            points = 2
        elif num_correct > 0:
            points = 1
        else:
            points = 0

        print("    Score: %d Feedback: %s" % (points, feedback))


def main(args):
    irsys = IRSystem()
    irsys.read_data('../data/RiderHaggard')
    irsys.index()
    irsys.compute_tfidf()

    if len(args) == 0:
        run_tests(irsys)
    else:
        query = " ".join(args)
        print("Best matching documents to '%s':" % query)
        results = irsys.query_rank(query)
        for docId, score in results:
            print("%s: %e" % (irsys.titles[docId], score))


if __name__ == '__main__':
    args = sys.argv[1:]
    main(args)

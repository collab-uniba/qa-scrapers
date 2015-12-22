
"""
    Compatible with Python 2 and Python 3
"""

import csv
import logging
import os
import re
from math import log

from dateutil.parser import parse as parse_date
from nltk import FreqDist
from nltk import PorterStemmer
from nltk import tokenize
from nltk import word_tokenize
from pydblite.pydblite import Base


class Discretizer:
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    linesep = '\n'

    def __init__(self, db_name, db_files):
        self.db_name = db_name
        self.db_files = db_files
        self.db = dict()

    def log(self, msg, level=logging.DEBUG):
        self.logger.log(level, msg)

    def load_db(self, check=True, fix=False, save_to_file=False):
        self.log('Opening {0} database(s)'.format(len(self.db_files)), logging.INFO)
        for db_name, db_file in self.db_files.items():
            _db = Base(db_file, save_to_file=save_to_file)
            _db.open()
            self.log('Database {0} opened, records #: {1}'.format(db_name, len(_db)), logging.DEBUG)
            self.db.update({db_name: _db})
            _db.create_index('uid')
            _db.create_index('type')
        if check is True:
            self.check_db(fix)

    """
    * fix answers_count with actual # of answers exported
    * if an answer has tag != N/A, the tags must be applied to the question in the same thread
    * if a question is marked as resolved True, then one of the answers in the thread must have been marked as solution;
    and viceversa;
    * check if Q or A text is ''
    * turn question uid from int to unicode string
    """

    def check_db(self, fix=False):
        self.log('Checking consistency for databases.', logging.INFO)
        for name, _db in self.db.items():
            for question in _db._type['question']:
                expected_answers_count = int(question['answers'])
                actual_answers_count = 0
                for i in range(1, expected_answers_count + 1):
                    try:
                        _db._uid[str(question['uid']) + '.' + str(i)][0]
                        actual_answers_count += 1
                    except IndexError:
                        break
                if actual_answers_count < expected_answers_count:
                    self.log('Fixing answers count mismatch in thread id {0}, expected {1}, found {2}'.
                             format(question['uid'], expected_answers_count, actual_answers_count))
                    _db.update(question, answers=actual_answers_count)

            for record in (_db('text') == ''):
                self.log('Warning on record {0} from db {1}: empty text!'.format(record['uid'], name),
                         logging.WARNING)

            for record in (_db('type') == 'answer') & (_db('tags') != 'N/A'):
                self.log('Warning on record {0} from db {1}: tags in answer!'.format(record['uid'], name),
                         logging.WARNING)
                question_uid = record['uid'].split('.')[0]
                question = _db._uid[question_uid][0]
                question_tags = question['tags'] + '.' + record['tags']
                _db.update(question, tags=question_tags)

            if fix is True:
                _db.commit()

    def load_threads(self):
        self.log('Loading threads from {0} db(s)'.format(len(self.db_files)), logging.INFO)
        overall_threads = list()
        for name, _db in self.db.items():
            db_threads = list()
            questions = _db._type['question']  # use db index
            self.log('Loaded {0} questions (threads) from db {1}, attaching answers...'.format(len(questions), name),
                     logging.DEBUG)
            for question in questions:
                answers = self._get_answers(question['uid'], int(question['answers']), _db)
                db_threads.append({'question': question, 'question_uid': question['uid'],
                                   'date_time': question['date_time'], 'answers_count': question['answers'],
                                   'resolved': question['resolve'], 'tags': question['tags'], 'answers': answers})

            overall_threads.extend(db_threads)
        self.log('Overall threads loaded: {0} from {1} database(s)'.format(len(overall_threads), len(self.db_files)))
        return overall_threads

    def _get_answers(self, question_id, answers_count, _db):
        self.log('Getting {0} answers for thread id {1}'.format(answers_count, question_id), logging.DEBUG)
        answers = list()
        if answers_count > 0:
            for i in range(1, answers_count + 1):
                answer_id = '{0}.{1}'.format(question_id, i)
                for answer in (_db._uid[answer_id]):  # use index
                    answers.append(answer)
            if answers_count != len(answers):
                self.log('Warning in thread id {0}: loaded {1} answers, expected {2}. Please, run a check db with '
                         'fix=True'.format(question_id, len(answers), answers_count),
                         logging.WARNING)
        return answers

    def compute_features(self, threads, stemmed_vocabulary, distrib_matrix):
        self.log('Computing features. Please, wait. This will take some serious time...', logging.INFO)
        for thread in threads:
            self.log('Computing features for thread id {0}'.format(thread['question_uid']), logging.INFO)
            try:
                base_date = parse_date(thread['date_time'])
            except ValueError:
                base_date = parse_date('1970-01-01')
            except AttributeError:
                base_date = thread['date_time']
            answers = thread['answers']
            tag_list = thread['tags'].split('.')
            if '' in tag_list:
                tag_list.remove('')
            for answer in answers:
                # compute thread tags
                answer_tags = answer['tags'].split()
                if 'N/A' in answer_tags:
                    answer_tags.remove('N/A')
                tag_list.extend(answer_tags)
                thread['tags'] = sorted(set(tag_list))

                # compute len in chars and words
                alen = len(answer['text'])
                answer['len'] = alen
                wordcount = Discretizer._count_words(answer['text'])
                answer['wordcount'] = wordcount
                if wordcount == 0:
                    answer['avg_chars_per_word'] = 0
                else:
                    answer['avg_chars_per_word'] = "{0:.2f}".format(alen / float(wordcount))  # float with 2 decimals
                try:
                    sentences = tokenize.sent_tokenize(answer['text'].decode('utf-8', 'replace').encode('ascii', 'replace'),
                                                       language='english')
                except (AttributeError, TypeError) as e:
                    sentences = tokenize.sent_tokenize(str(answer['text']), language='english')
                sentence_count = len(sentences)
                answer['sentences'] = sentence_count
                if sentence_count == 0:
                    words_per_sentence = 0
                else:
                    words_per_sentence = "{0:.2f}".format(wordcount / float(sentence_count))
                answer['avg_words_per_sentence'] = words_per_sentence
                longest_sentence = 0
                for s in sentences:
                    l = Discretizer._count_words(s)
                    if l > longest_sentence:
                        longest_sentence = l
                answer['longest_sentence'] = longest_sentence
                try:
                    creation_date = parse_date(answer['date_time'])
                except AttributeError:
                    creation_date = answer['date_time']
                time_difference = abs((creation_date - base_date).total_seconds())
                answer['time_difference'] = time_difference

                # TODO upvotes score

                # check for urls and code snippets
                match = re.search(r'http(s)?://', str(answer['text']), re.MULTILINE)
                if match:
                    answer['has_links'] = True
                else:
                    answer['has_links'] = False

                answer['has_code_snippet'] = self._has_codesnippet(str(answer['text']))
                try:
                    LL = Discretizer._log_likelihood(answer['text'].decode('utf-8', 'replace').encode('ascii', 'replace'),
                                             stemmed_vocabulary, distrib_matrix)
                except (AttributeError, TypeError) as e:
                    LL = Discretizer._log_likelihood(str(answer['text']), stemmed_vocabulary, distrib_matrix)
                answer['loglikelihood'] = LL
                answer['loglikelihood_descending'] = LL
                answer['loglikelihood_ascending'] = LL
                try:
                     aspw = Discretizer._ASPW(answer['text'].decode('utf-8', 'replace').encode('ascii', 'replace'))
                except (AttributeError, TypeError) as e:
                     aspw = Discretizer._ASPW(str(answer['text']))
                fk = Discretizer._FK(answer['avg_words_per_sentence'], aspw)
                answer['F-K'] = fk
                answer['F-K_descending'] = fk
                answer['F-K_ascending'] = fk

            # compute ranks
            answers = Discretizer._sort_rank(answers, 'upvotes', reverse=True)
            answers = Discretizer._sort_rank(answers, 'sentences', reverse=True)
            answers = Discretizer._sort_rank(answers, 'len', reverse=True)
            answers = Discretizer._sort_rank(answers, 'views', reverse=True)
            answers = Discretizer._sort_rank(answers, 'wordcount', reverse=True)
            answers = Discretizer._sort_rank(answers, 'avg_chars_per_word', reverse=True)
            answers = Discretizer._sort_rank(answers, 'avg_words_per_sentence', reverse=True)
            answers = Discretizer._sort_rank(answers, 'longest_sentence', reverse=True)
            answers = Discretizer._sort_rank(answers, 'time_difference', reverse=False)
            answers = Discretizer._sort_rank(answers, 'loglikelihood_descending', reverse=True)
            answers = Discretizer._sort_rank(answers, 'loglikelihood_ascending', reverse=False)
            answers = Discretizer._sort_rank(answers, 'F-K_descending', reverse=True)
            answers = Discretizer._sort_rank(answers, 'F-K_ascending', reverse=False)
            thread['answers'] = answers

        self.log('Done computing features for {0} threads'.format(len(threads)), logging.INFO)
        return threads

    @staticmethod
    def _ASPW(text):
        aspw = 0
        for word in text.split():
            s = Discretizer._count_syllables(word)
            aspw += s
        return aspw

    @staticmethod
    def _count_syllables(word):
        vowels = ['a', 'e', 'i', 'o', 'u', 'y']
        currentWord = list(word)
        numVowels = 0
        lastWasVowel = False
        for wc in currentWord:
            foundVowel = False
            for v in vowels:
                # don't count diphthongs
                if (v == wc) and lastWasVowel is True:
                    foundVowel = True
                    lastWasVowel = True
                    break
                elif (v == wc) and lastWasVowel is False:
                    numVowels += 1
                    foundVowel = True
                    lastWasVowel = True
                    break

            # If full cycle and no vowel found, set lastWasVowel to false;
            if not foundVowel:
                lastWasVowel = False

        # Remove es, it's _usually? silent
        if (len(word) > 2) and (word[len(word)-2:] == "es"):
            numVowels -= 1
        # remove silent e
        elif (len(word) > 1) and (word[len(word)-1:] == "e"):
            numVowels -= 1
        return numVowels

    @staticmethod
    def _FK(awps, asps):
        fk = (0.39 * float(awps)) + (11.8 * float(asps)) - 15.59
        return fk

    @staticmethod
    def _log_likelihood(answer_text, stemmed_vocabulary, distrib_matrix):
        LL = 0
        if answer_text is not '':
            tokens = word_tokenize(str(answer_text), language='english')
            porter_stemmer = PorterStemmer()
            unique_wordcount = len(stemmed_vocabulary)
            """
            per ogni w unica print_function words
                Cw = conta w in answer_text
                PwM = self.distrib_matrix[stemmer(w)]
                unique_wordcount = len(tokenize(answer_text)
            """
            for w in tokens:
                _w = w.strip().lower()
                Cw = 0
                for _ in answer_text.split():
                    if _w == _.strip().lower():
                        Cw += 1

                try:
                    w_stem = porter_stemmer.stem(_w.decode('utf-8', 'replace').encode('ascii', 'replace'))
                except AttributeError:
                    w_stem = porter_stemmer.stem(_w)
                try:
                    PwM = distrib_matrix[w_stem]
                except KeyError:  # key error means frequency is equal to cutoff point 1
                    PwM = 1
                LL += (Cw * log(float(PwM)))

            try:
                LL = "{0:.2f}".format(LL / float(unique_wordcount))
            except ZeroDivisionError:
                LL = 0 

        return LL

    @staticmethod
    def _count_words(text):
        wordcount = 0
        for word in text.split():
            wordcount += 1
        return wordcount

    @staticmethod
    def _sort_rank(answers, key, reverse=True):
        new_list = sorted(answers, key=lambda x: float(x[key]), reverse=reverse)
        ranks = dict()
        for i in range(0, len(answers)):
            ranks[new_list[i]['uid']] = i + 1

        # fix rank ties
        for i in range(0, len(answers)-1):
            if new_list[i][key] == new_list[i+1][key]:
                ranks[new_list[i+1]['uid']] = ranks[new_list[i]['uid']]

        for k, v in ranks.items():
            for a in answers:
                if a['uid'] == k:
                    a['{0}_rank'.format(key)] = v
        return answers

    def _has_codesnippet(self, text):
        code = False
        if re.search(r'({|}| package |\.jar| class | namespace |exception |<<| end | def |<\?php| soap | <xml| wsdl |\.cs|\.java|\.php|\.rb|lambda)',
                     text, re.MULTILINE | re.IGNORECASE):
                code = True
        return code

    def build_vocabulary(self, stems):
        vocabulary_filename = '{0}_vocabulary.txt'.format(self.db_name)
        if os.path.isfile(vocabulary_filename):  # load vocabulary from file
            words = list()
            self.log('Loading existing community vocabulary from {0}'.format(vocabulary_filename), logging.INFO)
            with open(vocabulary_filename, 'rt') as f:
                for word in f:
                    words.append(word.strip())
                f.close()
            vocabulary = sorted(set(words))
        else:  # create vocabulary and save file
            self.log('Creating new vocabulary into {0}. Please wait, this may take some time.'.
                     format(vocabulary_filename), logging.INFO)
            vocabulary = sorted(set(stems))
            with open(vocabulary_filename, 'wt') as f:
                for lemma in vocabulary:
                    f.write('{0}{1}'.format(lemma, self.linesep))
                f.close()
        return vocabulary

    def build_corpus(self):
        corpus_filename = '{0}_corpus.txt'.format(self.db_name)
        corpus = list()
        if os.path.isfile(corpus_filename):  # load corpus from file
            self.log('Loading existing corpus from {0}'.format(corpus_filename), logging.INFO)
            with open(corpus_filename, 'rt') as f:
                for word in f:
                    corpus.append(word.strip())
                f.close()
        else:
            self.log('Creating corpus from {0} database(s). Please wait, this may take some time.'.format(
                len(self.db_files)), logging.INFO)
            with open(corpus_filename, 'wt') as f:
                for name, _db in self.db.items():
                    self.log('Updating corpus from db {0}.'.format(name), logging.DEBUG)
                    for record in _db:
                        try:
                            tokens = word_tokenize(record['text'].decode('utf-8', 'replace').encode('ascii', 'replace'),
                                                   language='english')
                        except (AttributeError, TypeError) as e:
                            tokens = word_tokenize(str(record['text']), language='english')
                        for t in tokens:
                            corpus.append(t)
                            f.write('{0}{1}'.format(t, self.linesep))
                f.close()
        return corpus

    def build_stems(self, corpus):
        stems_filename = '{0}_stems.txt'.format(self.db_name)
        if os.path.isfile(stems_filename):  # load stems from file
            stems = list()
            self.log('Loading existing stems from {0}'.format(stems_filename), logging.INFO)
            with open(stems_filename, 'rt') as f:
                for stem in f:
                    stems.append(stem.strip())
                f.close()
        else:
            self.log('Creating stems from corpus into {0}. Please wait, this may take some time.'.format(
                stems_filename), logging.INFO)
            porter_stemmer = PorterStemmer()
            try:
                stems = [porter_stemmer.stem(token.lower().decode('utf-8', 'replace').encode('ascii', 'replace'))
                         for token in corpus]
            except (AttributeError, TypeError) as e:
                stems = [porter_stemmer.stem(token.lower())
                         for token in corpus]
            with open(stems_filename, 'wt') as f:
                for stem in stems:
                    f.write('{0}{1}'.format(stem, self.linesep))
                f.close()
        return stems

    def build_distribution_matrix(self, stems):
        distrib_matrix_filename = '{0}_distrib_matrix.txt'.format(self.db_name)
        if os.path.isfile(distrib_matrix_filename):  # load matrix from file
            self.log('Loading existing distribution matrix from {0}'.format(distrib_matrix_filename), logging.INFO)
            distrib_matrix = dict()
            with open(distrib_matrix_filename, 'rt') as f:
                csvrreader = csv.DictReader(f, delimiter=' ', lineterminator=self.linesep)
                for row in csvrreader:
                    distrib_matrix.update({row['w']: row['P(w|M)']})
                f.close()
        else:  # create matrix and save file
            self.log('Creating new distribution matrix into {0}. Please wait, this may take some time'.
                     format(distrib_matrix_filename), logging.INFO)
            distrib_matrix = FreqDist(stems)

            with open(distrib_matrix_filename, 'wt') as f:
                writer = csv.DictWriter(f, fieldnames=['w', 'P(w|M)'], delimiter=' ', lineterminator=self.linesep)
                writer.writeheader()
                for k in distrib_matrix.keys():
                    writer.writerow({'w': k, 'P(w|M)': distrib_matrix[k]})
                f.close()

        distrib_matrix = Discretizer.reduce_distribution_matrix(distrib_matrix, cutoff=1)
        return distrib_matrix

    @staticmethod
    def reduce_distribution_matrix(matrix, cutoff=1):
        reduced = {key: value for key, value in matrix.items() if int(value) > cutoff}
        return reduced

    def save_csv(self, threads):
        fout = '{0}_features.csv'.format(self.db_name)
        self.log('Saving features into {0}'.format(fout), logging.INFO)
        csvf = open(fout, 'wt')
        fields = ('resolved', 'question_uid', 'answers_count', 'answer_uid',
                  'date_time', 'time_difference', 'time_difference_rank', 'solution', 'len', 'len_rank', 'wordcount',
                  'wordcount_rank', 'avg_chars_per_word', 'avg_chars_per_word_rank', 'sentences', 'sentences_rank',
                  'avg_words_per_sentence', 'avg_words_per_sentence_rank', 'longest_sentence', 'longest_sentence_rank',
                  'views', 'views_rank', 'loglikelihood', 'loglikelihood_ascending_rank',
                  'loglikelihood_descending_rank', 'F-K', 'F-K_ascending_rank', 'F-K_descending_rank', 'upvotes',
                  'upvotes_rank', 'has_links', 'has_code_snippet', 'has_tags')
        writer = csv.DictWriter(csvf, dialect=csv.excel, fieldnames=fields, delimiter=';', lineterminator=self.linesep)
        writer.writeheader()
        # empty_line = dict.fromkeys(fields)
        for t in threads:
            row = dict()
            row.fromkeys(fields)
            answers = t['answers']
            # question with no answers are excluded
            i = 0
            for a in answers:
                i += 1
                if i == 1:
                    row['resolved'] = t['resolved']
                    row['question_uid'] = t['question_uid']
                    if len(t['tags']) > 0:
                        row['has_tags'] = True
                    else:
                        row['has_tags'] = False
                else:
                    row['resolved'] = ''
                    row['question_uid'] = ''
                row['answers_count'] = t['answers_count']
                row['answer_uid'] = a['uid']
                row['time_difference'] = a['time_difference']
                row['time_difference_rank'] = a['time_difference_rank']
                if a['resolve'] == 'solution':
                    row['solution'] = True
                else:
                    row['solution'] = False
                row['len'] = a['len']
                row['len_rank'] = a['len_rank']
                row['wordcount'] = a['wordcount']
                row['wordcount_rank'] = a['wordcount_rank']
                row['avg_chars_per_word'] = a['avg_chars_per_word']
                row['avg_chars_per_word_rank'] = a['avg_chars_per_word_rank']
                row['sentences'] = a['sentences']
                row['sentences_rank'] = a['sentences_rank']
                row['avg_words_per_sentence'] = a['avg_words_per_sentence']
                row['avg_words_per_sentence_rank'] = a['avg_words_per_sentence_rank']
                row['longest_sentence'] = a['longest_sentence']
                row['longest_sentence_rank'] = a['longest_sentence_rank']
                row['views'] = a['views']
                row['views_rank'] = a['views_rank']
                row['loglikelihood'] = a['loglikelihood']
                row['loglikelihood_descending_rank'] = a['loglikelihood_descending_rank']
                row['loglikelihood_ascending_rank'] = a['loglikelihood_ascending_rank']
                row['F-K'] = a['F-K']
                row['F-K_descending_rank'] = a['F-K_descending_rank']
                row['F-K_ascending_rank'] = a['F-K_ascending_rank']
                row['upvotes'] = a['upvotes']
                row['upvotes_rank'] = a['upvotes_rank']
                row['has_links'] = a['has_links']
                row['has_code_snippet'] = a['has_code_snippet']
                row['date_time'] = a['date_time']
                writer.writerow(row)
            #writer.writerow(empty_line)
        csvf.close()
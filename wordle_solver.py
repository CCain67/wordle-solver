import time
import pdb
import pandas as pd

# global variables
alphabet = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l',
            'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
wordle_small_txt = open("wordle-2315.txt", "r")
wordle_big_txt = open("wordle-12974.txt", "r")
wordle_small = wordle_small_txt.read().replace('\n', ' ').split(" ")
wordle_big = wordle_big_txt.read().replace('\n', ' ').split(" ")


def intersect(word_1, word_2) -> bool:
    for i in range(5):
        if word_1[i] == word_2[i]:
            return True
    return False


def num_intersect(word_1, word_2) -> int:
    return sum([word_1[i] == word_2[i] for i in range(5)])


def get_char_freq(char_freq_df, word: str) -> float:
    return sum([char_freq_df[i][word[i]] for i in range(5)])


class WordList:
    def __init__(self, list_of_words: list[str]):
        self.list_of_words = list_of_words

    def get_char_freq_df(self):
        c = {}

        for i in range(5):
            c[i] = [len([word for word in self.list_of_words if word[i] == char])
                    for char in alphabet]
        char_freq = pd.DataFrame(c, index=alphabet)/2315
        return char_freq

    def rank_guesses(self, scheme: str, j: int = 0):
        w = {}
        char_freq_df = self.get_char_freq_df()
        for word in self.list_of_words:
            if scheme == 'word_intersects':
                w[word] = 0
                for other_word in self.list_of_words:
                    w[word] += intersect(word, other_word)

            elif scheme == 'char_intersects':
                w[word] = get_char_freq(char_freq_df, word)

            elif scheme == 'char_word_ratio':
                i, n = 0, 0
                for other_word in self.list_of_words:
                    i += intersect(word, other_word)
                    n += num_intersect(word, other_word)
                w[word] = n/i
            else:
                print("ranking scheme must be one of the following:")
                print("'word_intersects', 'char_intersects', 'char_word_ratio'")
                return

        W = pd.Series(w, index=self.list_of_words).sort_values(
            ascending=False).astype('float64')
        return (W.index[j], W[j], W)

    def feature_df(self):
        w = {}
        char_freq_df = self.get_char_freq_df()
        for word in self.list_of_words:
            i, n, cf = 0, 0, get_char_freq(char_freq_df, word)
            for other_word in self.list_of_words:
                i += intersect(word, other_word)
                n += num_intersect(word, other_word)
            w[word] = (word, i, n, cf, n/i)

        W = pd.DataFrame(w, index=['word', 'word_intersects',
                         'char_intersects', 'char_freq', 'char_word_ratio']).transpose().reset_index(drop=True)
        return W


class Wordle:
    def __init__(self, answer_pool: WordList):
        self.answer_pool = answer_pool

    def char_eval(self, char: str, solution: str, position: int) -> str:
        if char == solution[position]:
            return 'correct'
        elif char in set(solution):
            return 'switch'
        else:
            return 'incorrect'

    def get_hint(self, guess: str, solution: str) -> list:
        correct, switches, incorrect_chars = {}, {}, set()
        for i in range(5):
            char = guess[i]
            result = self.char_eval(char, solution, i)
            if result == 'correct':
                correct[i] = char
            elif result == 'switch':
                switches[i] = char
            elif result == 'incorrect':
                incorrect_chars = incorrect_chars.union(char)

        return (correct, switches, incorrect_chars)

    def criteria_check(self, word: str, hint: list, incorrect_chars: set, incorrect_words: set) -> bool:
        correct, switches, incorrect = hint[0], hint[1], hint[2]

        incorrect_chars = incorrect.union(incorrect_chars)
        switch_set = set(switches.values())

        if word in incorrect_words:
            return False
        elif set(word).intersection(incorrect_chars) != set():
            return False
        elif not switch_set.issubset(set(word)):
            return False
        for position in switches.keys():
            if word[position] == switches[position]:
                return False
        for position in correct.keys():
            if word[position] != correct[position]:
                return False
        return True

    def new_guess(self, score: list, word_list: WordList, incorrect_chars: set, incorrect_words: set, scheme: str = 'char_intersects', j=0) -> list:
        L = [word for word in word_list.list_of_words if self.criteria_check(
            word, score, incorrect_chars, incorrect_words)]
        word_sublist = WordList(L)
        W = word_sublist.rank_guesses(scheme, j)
        return (W, incorrect_chars, word_sublist, W[2])

    def simulate(self, guess: str, solution: str, scheme: str, show_guess_path: bool = True) -> int:
        incorrect_chars = set()
        incorrect_words = set()
        num_guesses = 1
        word_sublist = self.answer_pool
        s = guess
        while guess != solution:
            incorrect_words = incorrect_words.union([guess])
            score = self.get_hint(guess, solution)
            incorrect_chars = incorrect_chars.union(score[1])

            guess_data = self.new_guess(
                score, word_sublist, incorrect_chars, incorrect_words, scheme, j=0)
            next_guess = guess_data[0][0]

            if (guess == next_guess and next_guess != self.solution):
                tries += 1
                guess_data = self.new_guess(
                    score, word_sublist, incorrect_chars, incorrect_words, scheme, tries)
                next_guess = guess_data[0][0]
                word_sublist = guess_data[2]
            else:
                tries = 0
                guess = next_guess
                word_sublist = guess_data[2]
            num_guesses += 1
            s = s + ' -> '+guess
        if show_guess_path == True:
            print(s)
        return num_guesses

    def full_simulation(self, guess: str, scheme: str, show_guess_path: bool = True):
        performance = {}
        tic = time.time()
        for solution in self.answer_pool.list_of_words:
            performance[solution] = self.simulate(
                guess, solution, scheme, show_guess_path)
        toc = time.time()
        p = pd.Series(performance)

        print("simulation time: ", toc-tic)
        print("mean guesses: ", p.mean())
        print("hardest word: ", p.index[p.argmax()])
        print("success rate: ", len(p[p <= 6])*100/len(p))
        print("failure rate: ", len(p[p > 6])*100/len(p))
        print("three or less: ", len(p[p <= 3])*100/len(p))
        print("only 2 guesses: ", len(p[p == 2]))
        return p.value_counts().sort_index()

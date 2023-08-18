"""This module defines the GuessScorer, WordleSolver, and WordleSimulator classes"""
from time import time

import pandas as pd
from scipy.stats import hmean

# global variables
ALPHABET = [
    "a",
    "b",
    "c",
    "d",
    "e",
    "f",
    "g",
    "h",
    "i",
    "j",
    "k",
    "l",
    "m",
    "n",
    "o",
    "p",
    "q",
    "r",
    "s",
    "t",
    "u",
    "v",
    "w",
    "x",
    "y",
    "z",
]

with open("data/wordle-2315.txt", "r", encoding="utf-8") as pool:
    ANSWER_POOL = pool.read().split("\n")


class GuessScorer:
    """Class which scores guesses against a fixed solution"""

    def __init__(self, solution: str) -> None:
        assert solution in ANSWER_POOL
        self.solution = solution

    def get_hint_string(self, guess: str) -> str:
        """Produces a hint string from a guess and a solution

        Example:
            guess: "train"
            solution: "chats"
            the hint string for the above pair is then: "swcww", since:
                "t" - is correct but needs its position switched,
                "r" - wrong, since there is no "r" in "chats",
                "a" - correct, since the letter is n the correct position in "chats",
                "i" - wrong, since there is no "i" in "chats",
                "n" - wrong, since there is no "n" in "chats"

        Returns:
            A string of length 5 consisting solely of "c", "s", and "w" characters.
        """
        assert guess in ANSWER_POOL
        hint_string = ""
        for i in range(5):
            if guess[i] == self.solution[i]:
                hint_string += "c"
            elif guess[i] in self.solution:
                hint_string += "s"
            else:
                hint_string += "w"
        return hint_string

    def score(self, guess: str) -> tuple:
        """Creates a tuple of data containing the result of evaluating the guess
        against the solution.

        Args:
            guess (str): the guess string
            solution (str): the solution string

        Returns:
            (dict, dict, set): a tuple containing:
                - the dictionary of correct letters {i:letter}
                - the dictionary of letters whose positions need to be switched {i:letter}
                - the set of incorrect letters
        """
        correct, switches, incorrect_chars = {}, {}, set()
        hint_str = self.get_hint_string(guess)
        for i, char in enumerate(guess):
            result = hint_str[i]
            if result == "c":
                correct[i] = char
            elif result == "s":
                switches[i] = char
            elif result == "w":
                incorrect_chars.update(char)

        return (correct, switches, incorrect_chars)


class WordleSolver:
    """Class which orchestrates a sequence of actions performed by a WordPoolOperator
    to produce a guess in a Wordle puzzle
    """

    def __init__(
        self,
        initial_guess: str = "slate",
        weights: dict = {char: 1 for char in ALPHABET},
    ) -> None:
        self.initial_guess = initial_guess
        self.weights = weights
        self.incorrect_chars = set()
        self.incorrect_words = set()

    def __repr__(self) -> str:
        return f"""
        initial_guess: {self.initial_guess}
        -------------
        weights: {self.weights}
        """

    def __eq__(self, other):
        if isinstance(other, WordleSolver):
            return (
                self.initial_guess == other.initial_guess
                and self.weights == other.weights
            )
        return False

    def __ne__(self, other):
        if isinstance(other, WordleSolver):
            return (
                self.initial_guess != other.initial_guess
                or self.weights != other.weights
            )
        return False

    def __hash__(self):
        return hash((self.initial_guess, frozenset(self.weights.items())))

    def get_char_freq(self, list_of_words: list[str]):
        """Given a list of 5 letter words, produces a dataframe with the alphabet as an index,
        and values being the count of how often each letter appeared in a word from the list in
        the given position
        """
        char_freq_dict = {char: [0] * 5 for char in ALPHABET}
        for word in list_of_words:
            for i, char in enumerate(word):
                char_freq_dict[char][i] += 1
        return char_freq_dict

    def criteria_check(self, word: str, score: tuple) -> bool:
        """Checks a word against the hint data and incorrect chars/words to see if it is a
        possible solution of a Wordle puzzle.
        """
        correct, switches = score[0], score[1]
        switch_set = set(switches.values())

        if word in self.incorrect_words:
            return False
        if set(word).intersection(self.incorrect_chars) != set():
            return False
        if not switch_set.issubset(set(word)):
            return False
        for position in switches.keys():
            if word[position] == switches[position]:
                return False
        for position in correct.keys():
            if word[position] != correct[position]:
                return False
        return True

    def reduce_wordpool(
        self,
        score: list,
        list_of_words: list[str],
    ) -> list:
        """Uses a score provided by a GuessScorer to eliminate words which cannot be a solution to a
        particular Wordle puzzle.
        """
        word_sublist = [
            word for word in list_of_words if self.criteria_check(word, score)
        ]
        return word_sublist

    def rank_guesses(self, list_of_words: list[str]) -> list:
        char_freq = self.get_char_freq(list_of_words)
        ranking_dict = {}

        for word in list_of_words:
            ranking_dict[word] = sum(
                (self.weights[word[i]] * char_freq[word[i]][i] for i in range(5))
            )

        ranking = sorted(ranking_dict.items(), key=lambda x: x[1], reverse=True)
        return [word for word, _ in ranking]

    def produce_guess(
        self,
        previous_guess: str,
        word_pool: list[str],
    ) -> int:
        if previous_guess is None:
            return self.initial_guess

        ranking = self.rank_guesses(word_pool)
        next_guess = ranking[0]
        if previous_guess == next_guess:
            next_guess = ranking[1]

        return next_guess


class WordleSimulator:
    """Class which sets up and orchestrates a Wordle Puzzle, or a collection of Wordle puzzles"""

    def simulate(self, solution: str, solver: WordleSolver):
        # Set the initial variables
        word_pool = ANSWER_POOL
        num_guesses = 0

        # Instantiate the scorer
        scorer = GuessScorer(solution)

        # Generate initial guess
        guess = solver.produce_guess(None, word_pool)
        guess_path = guess

        # Update info
        num_guesses += 1

        while guess != solution:
            score = scorer.score(guess)

            solver.incorrect_words.update([guess])
            solver.incorrect_chars.update(score[2])

            word_pool = solver.reduce_wordpool(score, word_pool)

            next_guess = solver.produce_guess(
                guess,
                word_pool,
            )
            guess = next_guess

            num_guesses += 1
            guess_path = guess_path + " -> " + guess

        return num_guesses, guess_path

    def partial_simulation(self, solver: WordleSolver, answer_subpool: list[str]):
        performance = {}

        for solution in answer_subpool:
            solver.incorrect_chars = set()
            solver.incorrect_words = set()
            performance[solution] = self.simulate(solution, solver)[0]

        return pd.Series(performance)

    def full_simulation(self, solver: WordleSolver):
        performance = {}

        for solution in ANSWER_POOL:
            solver.incorrect_chars = set()
            solver.incorrect_words = set()
            performance[solution] = self.simulate(solution, solver)[0]

        return pd.Series(performance)

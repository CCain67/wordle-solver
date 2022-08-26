from wordle_solver import *

pool = WordList(wordle_big)
wordle = Wordle(pool)

print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
guess = input("- Enter a starting guess: ")
if len(guess) != 5:
    guess = input("- Please enter a starting guess with 5 letters: ")
if guess not in wordle.answer_pool.list_of_words:
    guess = input(
        "- Please enter a starting guess in the answer pool (e.g. slate): ")
outcome = input("- Was that the answer? (yes/no): ")
outcome = 'no'
print("----------------------------------------------------------")

num_guesses = 1
word_sublist = wordle.answer_pool
incorrect_words = set([guess])
incorrect_chars = set()


def score_validate(score: str) -> bool:
    score_letters = set(['c', 's', 'w'])
    if len(score) != 5:
        print('The score needs to have length 5')
        return False
    elif not (set(score).union(score_letters)).issubset(score_letters):
        print('The score needs to be of the form XXXXX where each X can be:')
        print('c = correct, s = switch, or w = wrong')
        return False
    else:
        return True


# game
while outcome == 'no':

    # hint handling
    correct, switches = {}, {}
    result = input('- Enter score (e.g. scsws): ')
    while score_validate(result) == False:
        result = input('- Enter score (e.g. scsws): ')

    for i in range(5):
        char = result[i]
        if char == 'c':
            correct[i] = guess[i]
        elif char == 's':
            switches[i] = guess[i]
        elif char == 'w':
            incorrect_chars = incorrect_chars.union(guess[i])
    score = (correct, switches, incorrect_chars)

    # answer pool reduce
    guess_data = wordle.new_guess(
        score, wordle.answer_pool, incorrect_chars, incorrect_words, 'char_intersects')
    next_guess = guess_data[0].index[0]
    incorrect_chars = incorrect_chars.union(guess_data[1])
    word_sublist = guess_data[2]
    ranks = guess_data[0]

    print('- Incorrect chars: ', incorrect_chars)
    print('- Attempted words: ', incorrect_words)
    print('- Here are some options ('+str(len(ranks))+' total):')
    print(ranks.head(10))
    print('- For guess '+str(num_guesses)+' I suggest '+next_guess)
    print("----------------------------------------------------------")

    wordle = Wordle(word_sublist)
    guess = input('- What did you try? ')
    num_guesses += 1

    outcome = input("- Was that the answer? (yes/no): ")
    if outcome == 'no':
        incorrect_words = incorrect_words.union([guess])
    elif outcome == 'yes':
        print('\nlmao wordle is easy')
    print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")

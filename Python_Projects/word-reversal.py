#sentence randomizer
import random
sentence = "Hello world once again!"

def splitter():
    words = sentence.split()
    words = random.sample(words, len(words))
    for i in range(len(words)): #num of words
        char = list(words[i]) #split the selected word into a bunch of characters
        for j in range(len(char)): #num of characters in some word
            n = random.randint(1,10)
            if n < 5:
                char[j]=char[j].upper()
            else:
               char[j].lower
        words[i] = "".join(char) #join turns the list of characters back into a string
    print(words)
splitter()

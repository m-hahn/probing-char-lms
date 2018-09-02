unigrams = {}


if True:
 pathIn = "/private/home/mhahn/data/WIKIPEDIA/enwiki/english-train-tagged.txt"
 pathOut = "/private/home/mhahn/data/WIKIPEDIA/enwiki/english-wiki-word-vocab.txt"
elif False:
 assert False
 pathIn = "/private/home/mhahn/data/WIKIPEDIA/german-train-tagged.txt"
 pathOut = "/private/home/mhahn/data/WIKIPEDIA/german-wiki-word-vocab.txt"
else:
 assert False
 pathIn = "/checkpoint/mbaroni/char-rnn-exchange/tagged_italian_training_corpus.txt"
 pathOut = "/private/home/mhahn/data/WIKIPEDIA/itwiki/italian-wiki-word-vocab.txt"

import random
with open(pathIn, "r") as inFile:
   for line in inFile:
      line = line[:-1]
      index = line.find("\t")
      if index == -1:
#         print(line)
         continue
      word = line[:index].lower()
      unigrams[word] = unigrams.get(word, 0) + 1
 #     if random.random() > 0.99:
#          break
unigrams = sorted(list(unigrams.items()), key=lambda x:x[1],reverse=True)
with open(pathOut, "w") as outFile:
  for word, count in unigrams:
      print(f"{word}\t{count}", file=outFile)
      

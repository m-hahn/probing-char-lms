# python detectBoundariesUnit_Hidden_ExtractPattern_NoWhitespace_Classifier.py --language english  --batchSize 128 --char_dropout_prob 0.001 --char_embedding_size 200 --char_noise_prob 0.0 --hidden_dim 1024 --language english --layer_num 3 --learning_rate 3.6  --myID 282506230 --load-from wiki-english-nospaces-bptt-282506230 --weight_dropout_hidden 0.01 --weight_dropout_in 0.0

# python detectBoundariesUnit_Hidden_ExtractPattern_NoWhitespace_Classifier.py --batchSize 128 --char_dropout_prob 0.001 --char_embedding_size 100 --char_noise_prob 0.0 --hidden_dim 1024 --language german --layer_num 2 --learning_rate 2.0 --weight_dropout_hidden 0.05 --weight_dropout_in 0.01 --load-from wiki-german-nospaces-bptt-910515909

# python detectBoundariesUnit_Hidden_ExtractPattern_NoWhitespace_Classifier.py --batchSize 128 --char_dropout_prob 0.0 --char_embedding_size 200 --char_noise_prob 0.0 --hidden_dim 1024 --language italian --layer_num 2 --learning_rate 3.5  --weight_dropout_hidden 0.05 --weight_dropout_in 0.0 --load-from wiki-italian-nospaces-bptt-855947412

# German
#neuron = 1519 #1994


# Neuron selected using detectBoundariesUnit_Hidden.py


from paths import WIKIPEDIA_HOME
from paths import LOG_HOME
from paths import CHAR_VOCAB_HOME
from paths import MODELS_HOME
import sys

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--language", dest="language", type=str)
parser.add_argument("--load-from", dest="load_from", type=str)

import random
random.seed(1) # May nonetheless not be reproducible, since the classifier library doesn't seem to allow setting the seed

parser.add_argument("--batchSize", type=int, default=16)
parser.add_argument("--char_embedding_size", type=int, default=100)
parser.add_argument("--hidden_dim", type=int, default=1024)
parser.add_argument("--layer_num", type=int, default=1)
parser.add_argument("--weight_dropout_in", type=float, default=0.01)
parser.add_argument("--weight_dropout_hidden", type=float, default=0.1)
parser.add_argument("--char_dropout_prob", type=float, default=0.33)
parser.add_argument("--char_noise_prob", type = float, default= 0.01)
parser.add_argument("--learning_rate", type = float, default= 0.1)
parser.add_argument("--myID", type=int, default=random.randint(0,1000000000))
parser.add_argument("--sequence_length", type=int, default=80)


args=parser.parse_args()
print(args)

if args.language == "english":
  # Engish:
  neuron = [2044, 2517, 2841, 2331, 2611]
elif args.language == "german":
  # German
  neuron = [1519, 2029, 1094, 1379, 1451]
else:
  # Italian
  neuron = [1508, 1746, 1598, 1637, 1814]





#assert args.language == "german"


import corpusIteratorWikiWords



def plus(it1, it2):
   for x in it1:
      yield x
   for x in it2:
      yield x

try:
   with open(CHAR_VOCAB_HOME+"/char-vocab-wiki-"+args.language, "r") as inFile:
     itos = inFile.read().strip().split("\n")
except FileNotFoundError:
    assert False
    print("Creating new vocab")
    char_counts = {}
    # get symbol vocabulary

    with open(WIKIPEDIA_HOME+"/"+args.language+"-vocab.txt", "r") as inFile:
      words = inFile.read().strip().split("\n")
      for word in words:
         for char in word.lower():
            char_counts[char] = char_counts.get(char, 0) + 1
    char_counts = [(x,y) for x, y in char_counts.items()]
    itos = [x for x,y in sorted(char_counts, key=lambda z:(z[0],-z[1])) if y > 50]
    with open(CHAR_VOCAB_HOME+"/char-vocab-wiki-"+args.language, "w") as outFile:
       print("\n".join(itos), file=outFile)
#itos = sorted(itos)
#itos.append(" ")
#assert " " in itos
print(itos)
stoi = dict([(itos[i],i) for i in range(len(itos))])




import random


import torch

print(torch.__version__)

from weight_drop import WeightDrop


rnn = torch.nn.LSTM(args.char_embedding_size, args.hidden_dim, args.layer_num).cuda()

rnn_parameter_names = [name for name, _ in rnn.named_parameters()]
print(rnn_parameter_names)
#quit()


rnn_drop = WeightDrop(rnn, [(name, args.weight_dropout_in) for name, _ in rnn.named_parameters() if name.startswith("weight_ih_")] + [ (name, args.weight_dropout_hidden) for name, _ in rnn.named_parameters() if name.startswith("weight_hh_")])

output = torch.nn.Linear(args.hidden_dim, len(itos)+3).cuda()

char_embeddings = torch.nn.Embedding(num_embeddings=len(itos)+3, embedding_dim=args.char_embedding_size).cuda()

logsoftmax = torch.nn.LogSoftmax(dim=2)

train_loss = torch.nn.NLLLoss(ignore_index=0)
print_loss = torch.nn.NLLLoss(size_average=False, reduce=False, ignore_index=0)
char_dropout = torch.nn.Dropout2d(p=args.char_dropout_prob)

modules = [rnn, output, char_embeddings]
def parameters():
   for module in modules:
       for param in module.parameters():
            yield param

parameters_cached = [x for x in parameters()]

optim = torch.optim.SGD(parameters(), lr=args.learning_rate, momentum=0.0) # 0.02, 0.9

named_modules = {"rnn" : rnn, "output" : output, "char_embeddings" : char_embeddings, "optim" : optim}

if args.load_from is not None:
  checkpoint = torch.load(MODELS_HOME+"/"+args.load_from+".pth.tar")
  for name, module in named_modules.items():
      module.load_state_dict(checkpoint[name])

from torch.autograd import Variable


# ([0] + [stoi[training_data[x]]+1 for x in range(b, b+sequence_length) if x < len(training_data)]) 

#from embed_regularize import embedded_dropout


def prepareDatasetChunks(data, train=True):
      numeric = [0]
      boundaries = [None for _ in range(args.sequence_length+1)]
      boundariesAll = [None for _ in range(args.sequence_length+1)]

      count = 0
      currentWord = ""
      print("Prepare chunks")
      for chunk in data:
          print(len(chunk))
          for word in chunk:
#             assert word != "popula"
             for char in word:
                if boundariesAll[len(numeric)] is None:
                      boundariesAll[len(numeric)] = currentWord
       
                count += 1
                currentWord += char
                numeric.append((stoi[char]+3 if char in stoi else 2) if (not train) or random.random() > args.char_noise_prob else 2+random.randint(0, len(itos)))
                if len(numeric) > args.sequence_length:
                   yield numeric, boundaries, boundariesAll
                   numeric = [0]
                   boundaries = [None for _ in range(args.sequence_length+1)]
                   boundariesAll = [None for _ in range(args.sequence_length+1)]
      
             assert currentWord == word, (currentWord, word)
             boundaries[len(numeric)] = currentWord
             boundariesAll[len(numeric)] = currentWord
       
             currentWord = ""
       
  

# from each bath element, get one positive example OR one negative example

wordsSoFar = set()
hidden_states = []
labels = []
relevantWords = []
relevantNextWords = []
labels_sum = 0

def forward(numeric, train=True, printHere=False):
      global labels_sum
      numeric, boundaries, boundariesAll = zip(*numeric)

      numeric_selected = numeric
      input_tensor = Variable(torch.LongTensor(numeric_selected).transpose(0,1)[:-1].cuda(), requires_grad=False)
      target_tensor = Variable(torch.LongTensor(numeric_selected).transpose(0,1)[1:].cuda(), requires_grad=False)

      embedded = char_embeddings(input_tensor)

      hidden = None
      print(len(embedded))
      for i in range(40, len(embedded)):
            out, hidden = rnn_drop(embedded[i].unsqueeze(0), hidden)
            for j in range(len(embedded[0])):
                 nextRelevantWord = ([boundaries[j][k] for k in range(i+2, len(boundaries[j])) if boundaries[j][k] is not None]+["END_OF_SEQUENCE"])[0]
                 if nextRelevantWord == "END_OF_SEQUENCE":
                    continue
                 target = 1 if boundaries[j][i+1] is not None else 0
                 if abs(target+labels_sum - len(labels)/2) > 2:
                    continue
                 hidden_states.append((hidden[1][:,j,:].flatten()[neuron[0]]).unsqueeze(0).cpu().detach().numpy())
#                 hidden_states.append((hidden[1][:,j,:].flatten()[neuron]).cpu().detach().numpy())

                 labels.append(target)
                 labels_sum += labels[-1]

                 relevantWords.append(boundariesAll[j][i+1])
                 
                 relevantNextWords.append(nextRelevantWord)
                 assert boundariesAll[j][i+1] is not None
                 if j == 0:
                   print(hidden_states[-1], labels[-1], relevantWords[-1], relevantNextWords[-1])  
                 if (labels[-1] == 0) and not relevantNextWords[-1].startswith(relevantWords[-1]):
                     assert False, (relevantWords[-1], relevantNextWords[-1], list(zip(boundaries[j][i:], boundariesAll[j][i:])))
                 if (labels[-1] == 1) and relevantNextWords[-1].startswith(relevantWords[-1]): # this is actually not a hard assertion, it should just be quite unlikely in languages such as English
                     print("WARNING", list(zip(boundaries[j][i:], boundariesAll[j][i:])))
#                     if len(relevantWords[-1]) > 1:
 #                       assert False 

import time

devLosses = []
#for epoch in range(10000):
if True:
   training_data = corpusIteratorWikiWords.dev(args.language)
   print("Got data")
   training_chars = prepareDatasetChunks(training_data, train=True)



   rnn_drop.train(False)
   startTime = time.time()
   trainChars = 0
   counter = 0
   while True:
      counter += 1
      try:
         numeric = [next(training_chars) for _ in range(args.batchSize)]
      except StopIteration:
         break
      printHere = (counter % 50 == 0)
      forward(numeric, printHere=printHere, train=True)
      #backward(loss, printHere)
      if printHere:
          print((counter))
          print("Dev losses")
          print(devLosses)
          print("Chars per sec "+str(trainChars/(time.time()-startTime)))

      if len(labels) > 1000:
         break
  

predictors = hidden_states
dependent = labels


TEST_FRACTION = 0.0

from sklearn.model_selection import train_test_split
x_train, x_test, y_train, y_test, words_train, words_test, next_words_train, next_words_test = train_test_split(predictors, dependent, relevantWords, relevantNextWords, test_size=TEST_FRACTION, random_state=random.randint(1,100), shuffle=True)


from sklearn.linear_model import LogisticRegression

print("regression")

logisticRegr = LogisticRegression()

logisticRegr.fit(x_train, y_train)


errors = []
scores = []

examples_count = 0

for batch in range(100): # Go through the entire remainder of the Dev set

     hidden_states = []
     labels = []
     relevantWords = []
     relevantNextWords = []
     labels_sum = 0
     
     
     devLosses = []
     #for epoch in range(10000):
     if True:
     
     
        rnn_drop.train(False)
        startTime = time.time()
        trainChars = 0
        counter = 0
        while True:
           counter += 1
           try:
              numeric = [next(training_chars) for _ in range(args.batchSize)]
           except StopIteration:
              break
           printHere = (counter % 50 == 0)
           forward(numeric, printHere=printHere, train=True)
           #backward(loss, printHere)
           if printHere:
               print((counter))
               print("Dev losses")
               print(devLosses)
               print("Chars per sec "+str(trainChars/(time.time()-startTime)))
     
           if len(labels) > 10000:
              break
     if len(hidden_states) == 0:
          break
     predictors = hidden_states
     dependent = labels
     
     x_test = predictors
     y_test = dependent
     words_test = relevantWords
     next_words_test = relevantNextWords
     
   #  for i in range(len(x_test)):
    #     print(y_test[i], words_test[i], next_words_test[i])
     
     
     
     predictions = logisticRegr.predict(x_test)
     
     
     score = logisticRegr.score(x_test, y_test)
     scores.append(score)

     for i in range(len(predictions)):
         if predictions[i] != y_test[i]:
               errors.append((y_test[i], (words_test[i], next_words_test[i], predictions[i], y_test[i])))
     print("Balance ",sum(y_test)/len(y_test))
     examples_count += len(y_test)

falsePositives = {}
falseNegatives = {}
for error in errors:
   if error[0] == 0:
      record = error[1][0]+"|"+error[1][1]
      falsePositives[record] = falsePositives.get(record, 0)+1
   elif error[0] == 1:
      record = error[1][0]+" "+error[1][1]
      falseNegatives[record] = falseNegatives.get(record, 0)+1
      #assert error[1][0] != error[1][1], error

falsePositives = sorted(list(falsePositives.items()), key=lambda x:x[1])
falseNegatives = sorted(list(falseNegatives.items()), key=lambda x:x[1])

print(f"results/segmentation-{args.language}-frequent-errors-neuron-disjoint.txt")
with open(f"results/segmentation-{args.language}-frequent-errors-neuron-disjoint.txt", "w") as outFile:
   print("False Positives", file=outFile)
   for error in falsePositives[-100:]:
      print(error[0]+"\t"+str(error[1]), file=outFile)

   print("", file=outFile)   
   print("False Negatives", file=outFile)
   for error in falseNegatives[-100:]:
      print(error[0]+"\t"+str(error[1]), file=outFile)


print(examples_count)
score = sum(scores)/len(scores)
print(score)
print(batch)


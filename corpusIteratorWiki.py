import random
 

def load(language, partition):
  if language == "italian":
    with open("/private/home/mhahn/data/WIKIPEDIA/"+language+"-"+partition+".txt", "r") as inFile:
       print("Reading data file")
       data = inFile.read().strip().lower().split("\n")
       print("Shuffling")
       random.shuffle(data)
       print("Finished shuffling")
       return "".join(data)
  else:
    chunks = []
    with open("/private/home/mhahn/data/WIKIPEDIA/"+language+"-"+partition+".txt", "r") as inFile:
      for line in inFile:
        chunks.append(line.strip().lower())
        if len(chunks) > 10000:
           random.shuffle(chunks)
           yield "".join(chunks)
           chunks = []
    yield "".join(chunks)

def training(language):
  return load(language, "train")
#   with open("/private/home/mhahn/data/WIKIPEDIA/"+language+"-train.txt", "r") as inFile:
#     data = inFile.read().strip().lower().split("\n")
#     print("Shuffling")
#     random.shuffle(data)
#     print("Finished shuffling")
#     return "".join(data)
def dev(language):
  return load(language, "valid")
#   with open("/private/home/mhahn/data/WIKIPEDIA/"+language+"-valid.txt", "r") as inFile:
#     data = inFile.read().strip().lower().split("\n")
#     print("Shuffling")
#     random.shuffle(data)
#     print("Finished shuffling")
#     return "".join(data)
#

#     for line in data:
#        yield line


import re
from datasets import NUMBERS

RE_NUMBER = r"((^[0-9]*\.[0-9]+)|[0-9]+)$"


def get_number(token, default=None):
  return NUMBERS.get(re.sub(r"[-./,]", "", token.lower()), default)


def remove_hyphens(text):
  tokens = []

  for token in text.split():
    if "-" in token:
      words = token.split("-")
      numbers = [get_number(word) for word in words]
      if numbers.count(None) == 0:
        tokens.extend(words)
        continue

    tokens.append(token)

  return tokens


def convert_numeric_articles(old_tokens):
  new_tokens = []

  n = len(old_tokens)

  for i in range(n - 1):
    cur = old_tokens[i]
    nxt = old_tokens[i + 1]

    if cur.lower() == "a" and get_number(nxt):
      continue
    else:
      new_tokens.append(cur)

  new_tokens.append(old_tokens[-1])

  return new_tokens


def remove_decimal(token):
  if re.match(RE_NUMBER, token):
    if float(token) % 1 == 0:
      return str(int(float(token)))
    else:
      return str(float(token))

  return token


def find_ceil(n):
  for multiple in [100, 1000, 1000000, 1000000000, 1000000000000]:
    if n // multiple == 0:
      return multiple
  return 1
  

def evaluate(buf):
  multiples = {1000, 1000000, 1000000000, 1000000000000}

  while len(buf) > 1:
    cur = float(buf[0])
    nxt = float(buf[1])
    nxt2 = len(buf) > 2 and float(buf[2])

    # "three fourth"
    if 0 <= cur <= 9 and nxt % 1 != 0:
      buf[0] = cur * nxt
      del buf[1]
      continue

    # "twenty-two-million, three-hundred-fifty-five"
    if nxt in multiples and nxt2 not in multiples:
      if len(buf) > 3:
        buf[2] = evaluate(buf[2:])
        del buf[3:]
        continue


    # "five ninety eight"
    if cur < nxt:
      if nxt not in {100, 1000, 1000000, 1000000000, 1000000000000}:
        buf[0] = cur * find_ceil(nxt)
        continue
      else:
        buf[0] = cur * nxt

    else:
      buf[0] = cur + nxt

    del buf[1]

  return float(buf[0])


def combine_numbers(tokens):
  buf = []
  combined = []

  for token in tokens:
    if re.match(RE_NUMBER, token):
      buf.append(token)
      continue

    if buf:
      combined.append(str(evaluate(buf)))
      buf = []

    combined.append(token)

  if buf:
    combined.append(str(evaluate(buf)))

  return combined


def combine_symbols(tokens):
  combined = []

  for token in tokens:
    if m := re.match(r"^([0-9]+)/([0-9]+)$", token):
        p = int(m.group(0))
        q = int(m.group(1))
        combined.append(str(p / q))
        continue

    combined.append(token)

  return combined



def convert_word_to_number(text):
  # split at hyphens
  tokens = remove_hyphens(text)

  # remove "a" when followed by a number word
  tokens = convert_numeric_articles(tokens)

  text = " ".join([str(get_number(token, token)) for token in tokens])
  text = re.sub(r"(\d+?),(\d+?)", r"\1\2", text)
  text = re.sub(r"(\d+)\s+and\s+(\d+)", r"\1 \2", text)
  text = re.sub(r"(\d+)\s+of\s+(\d+)", r"\1/\2", text)
  text = re.sub(r"(\d+)\s+out of\s+(\d+)", r"\1/\2", text)
  text = re.sub(r"(\d+)\s+point\s+(\d+)", r"\1.\2", text)
  text = re.sub(r"(?:\b|\s+)point\s+(\d+)", r"0.\1", text)

  tokens = text.split()
  tokens = combine_numbers(tokens)
  tokens = combine_symbols(tokens)

  return " ".join([remove_decimal(token) for token in tokens])

# ======== TESTING ======== #
word_to_num = convert_word_to_number

# DECIMALS
# <num> point <num>
# four point five => 4.5
assert word_to_num("four point five") == "4.5"
assert word_to_num("4 point five") == "4.5"
assert word_to_num("four point 5") == "4.5"
assert word_to_num("4 point 5") == "4.5"

# point <num>
# point three => 0.3
assert word_to_num("zero point three") == "0.3"
assert word_to_num("point three") == "0.3"
assert word_to_num("two hundred and 5 point three") == "205.3"
assert word_to_num("nine million three forty 5 point three") == "9000345.3"
assert word_to_num("point 3") == "0.3"
assert word_to_num(". three") == ". 3"
assert word_to_num(". 3") == ". 3"


# HYPHEN
assert word_to_num("I, along with my friend, went to Chick-Fil-A and ordered two twenty-three burgers") == "I, along with my friend, went to Chick-Fil-A and ordered 223 burgers"
assert word_to_num("two-hundred") == "200"
assert word_to_num("twenty-five-hundred") == "2500"
assert word_to_num("twenty-two-million, three-hundred-fifty-five") == "22000355"

# COMMAS
assert word_to_num("5,000,000") == "5000000"
assert word_to_num("500,000") == "500000"
assert word_to_num("500, 40") == "500, 40"
assert word_to_num("50, 100.4") == "50, 100.4"
assert word_to_num("3,423") == "3423"
assert word_to_num("342,3") == "3423" # ????

# MISC
assert word_to_num("twenty three hundred") == "2300"
assert word_to_num("three sixty five") == "365"
assert word_to_num("four fifth") == "0.8"
assert word_to_num("a hundred") == "100"
assert word_to_num("a couple") == "2"
assert word_to_num("a couple donuts") == "2 donuts"
assert word_to_num("a couple thousand donuts") == "2000 donuts"
assert word_to_num("two million three hundred thousand and four") == "2300004"
assert word_to_num("seven billion three hundred and seventy seven million five hundred thousand eight thirty four") == "7377500834"
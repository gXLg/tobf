# prints a string in a most effective way in brainfuck
# and cleans up after itself

def string(s):
  byt = [*s.encode()]
  p = ""
  d = 0
  for i in byt:
    p += number((i - d) % 256) + "."
    d = i
  p += "[-]"

  byt = byt[::-1]
  q = ">".join(map(number, byt)) + "[.[-]<]"
  if len(q) < len(p): p = q
  for a in range(2, 256):
    q = number(a) + "["
    e = ""
    for i in byt:
      # b+ c+
      b, c = divmod(i, a)
      r = ">" + b * "+"
      s = ">" + c * "+"

      # b+ c-
      b, c = divmod(i, a)
      b, c = b + 1, a - c
      t = ">" + b * "+"
      u = ">" + c * "-"
      if len(t + u) < len(r + s):
        r, s = t, u

      # b- c-
      b, c = divmod(256 - i, a)
      t = ">" + b * "-"
      u = ">" + c * "-"
      if len(t + u) < len(r + s):
        r, s = t, u

      # b- c+
      b, c = divmod(256 - i, a)
      b, c = b + 1, a - c
      t = ">" + b * "-"
      u = ">" + c * "+"
      if len(t + u) < len(r + s):
        r, s = t, u

      q += r
      e += s
    q += "<" * len(byt) + "-]" + e + "[.[-]<]"
    if len(q) < len(p): p = q

  return p

# effectively storing number:
# number = a * b + c
def number(n):
  n = n % 256
  p = n * "+"
  q = (256 - n) * "-"
  if len(q) < len(p): p = q

  for a in range(2, 256):
    # b+ c+
    b, c = divmod(n, a)
    q = ">" + a * "+" + "[<" + b * "+" + ">-]<" + c * "+"
    if len(q) < len(p): p = q

    # b+ c-
    b, c = divmod(n, a)
    b, c = b + 1, a - c
    q = ">" + a * "+" + "[<" + b * "+" + ">-]<" + c * "-"
    if len(q) < len(p): p = q

    # b- c-
    b, c = divmod(256 - n, a)
    q = ">" + a * "+" + "[<" + b * "-" + ">-]<" + c * "-"
    if len(q) < len(p): p = q

    # b- c+
    b, c = divmod(256 - n, a)
    b, c = b + 1, a - c
    q = ">" + a * "+" + "[<" + b * "-" + ">-]<" + c * "+"
    if len(q) < len(p): p = q

  return p

def clean(code):
  code = "".join([i for i in code if i in "+-<>[].,@"])

  b = 0
  for index, char in enumerate(code):
    if char == "[": b += 1
    elif char == "]": b -= 1
    if b < 0:
      exit(f"Unmatched bracket at {index}")
  if b:
    exit("A bracket never closes")

  old = ""
  while old != code:
    old = code
    code = code.replace("+-", "")
    code = code.replace("-+", "")
    code = code.replace("><", "")
    code = code.replace("<>", "")
    code = code.replace("+,", ",")
    code = code.replace("-,", ",")

  while "][" in code:
    c = code.index("][") + 1
    a = c
    b = 1
    while b:
      c += 1
      if code[c] == "]": b -= 1
      if code[c] == "[": b += 1
    code = code[:a] + code[c + 1:]

  return code
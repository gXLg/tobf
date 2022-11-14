import effective
import re

def lexer(f):
  tokens = {
    "\\=": "ASS",
    "\\+": "ADD",
    "\\-": "SUB",
    "\\(": "LBR",
    "\\)": "RBR",
    "\\*\\*": "POW",
    "\\*": "MUL",
    "\\/": "DIV",
    "\\%": "MOD",
    "0|([1-9][0-9]*)": "NUM",
    "[_a-zA-Z][_a-zA-Z0-9]*": "VAR",
    "[\\t\\v ]": "WSP",
    "\\#": "OFF"
  }

  tt = []
  while f:
    for t in tokens:
      r = re.search(t, f)
      if not r: continue
      if r.span()[0] != 0: continue
      s = f[:r.span()[1]]
      f = f[r.span()[1]:]
      if tokens[t] == "WSP": continue
      tt.append([s, tokens[t]])
      break
  tt.append(["", "END"])
  return tt

class Parser:
  def __init__(self, tokens):
    self.current = None
    self.tokens = tokens
    self.n()

  def n(self):
    self.current = self.tokens.pop(0)

  def parse(self):
    if self.current[1] == "END":
      exit("Empty expression!")
    res = self.assign()
    if self.current[1] != "END":
      exit("Could not parse!")
    return res

  def assign(self):
    res = self.expr()
    while self.current[1] != "END" and self.current[1] == "ASS":
      token = self.current
      self.n()
      res = BinOp(res, token, self.expr())
    return res

  def expr(self):
    res = self.mod()
    while self.current[1] != "END" and self.current[1] in ["ADD", "SUB"]:
      token = self.current
      self.n()
      res = BinOp(res, token, self.mod())
    return res

  def mod(self):
    res = self.term()
    while self.current[1] != "END" and self.current[1] == "MOD":
      token = self.current
      self.n()
      res = BinOp(res, token, self.term())
    return res

  def term(self):
    res = self.power()
    while self.current[1] != "END" and self.current[1] in ["MUL", "DIV"]:
      token = self.current
      self.n()
      res = BinOp(res, token, self.power())
    return res

  def power(self):
    res = self.offset()
    while self.current[1] != "END" and self.current[1] == "POW":
      token = self.current
      self.n()
      res = BinOp(res, token, self.offset())
    return res

  def offset(self):
    res = self.factor()
    while self.current[1] != "END" and self.current[1] == "OFF":
      token = self.current
      self.n()
      res = BinOp(res, token, self.factor())
    return res

  def factor(self):
    token = self.current

    if token[1] == "LBR":
      self.n()
      res = self.assign()
      if self.current[1] != "RBR":
        exit("Not closed bracket!")
      self.n()
      return res
    elif token[1] in ["VAR", "NUM"]:
      self.n()
      return Value(token)
    elif token[1] == "ADD":
      self.n()
      return self.factor()
    elif token[1] == "SUB":
      self.n()
      return BinOp(Value(["0", "NUM"]), token, self.factor())
    elif token.type == "END":
      return None
    else:
      exit("Illegal token here!")

class BinOp:
  def __init__(self, left, token, right):
    self.left = left
    self.token = token
    self.right = right

  def __repr__(self):
    return f"({self.left}{self.token[0]}{self.right})"

  def visit(self, brain, offset):
    code = ""
    match self.token[1]:
      case "ADD":
        code += self.left.visit(brain, offset)
        code += ">"
        code += self.right.visit(brain, offset + 1)
        code += "[-<+>]"
        code += "<"
      case "SUB":
        code += self.left.visit(brain, offset)
        code += ">"
        code += self.right.visit(brain, offset + 1)
        code += "[-<->]"
        code += "<"
      case "MUL":
        code += ">"
        code += self.left.visit(brain, offset + 1)
        code += ">>"
        code += self.right.visit(brain, offset + 3)
        code += "[-<<[->+<]>[-<+<+>>]>]<"
        code += "<[-]<"
      case "DIV":
        code += self.left.visit(brain, offset)
        code += ">>"
        code += self.right.visit(brain, offset + 2)
        code += "<<"
        code += "[>+>-[>>>]<[[>+<-]>>+>]<<<<-]"
        code += ">[-]>[-]>[-<<<+>>>]<<<"
      case "MOD":
        code += self.left.visit(brain, offset)
        code += ">>"
        code += self.right.visit(brain, offset + 2)
        code += "<<"
        code += "[>+>-[>>>]<[[>+<-]>>+>]<<<<-]"
        code += ">>[-]>[-]<<[-<+>]<"
      case "POW":
        code += "+>>"
        code += self.left.visit(brain, offset + 2)
        code += ">>>"
        code += self.right.visit(brain, offset + 5)
        code += "[-<<<[->+<]>[-<+>>+<]<<[-]<[->+<]>"
        code += ">>>[-<<<[->>+<<]>>[-<<+<+>>>]>]>]"
        code += "<<<[-]<[-]<"
      case "OFF":
        if self.left.token[1] != "VAR":
          exit("Offset from expression failure")
        code += self.right.visit(brain, offset)
        v = self.left.token[0]
        x = brain.get_var(v)
        d = brain.pointer + offset - x - 3
        e = brain.pointer + offset - x - 1

        code += "[-" + "<" * d + "+<<+"
        code += ">" * e + "]" + "<" * e
        # moving to the cell and copying index
        code += "[->>[->>+<<]<<[->>+<<]>>]"
        # copying cell into runner
        code += "<[->+>>>>+<<<<<]>>>>>[-<<<<<+>>>>>]<<<<"
        # moving back and decreasing index copy
        code += ">>[-<<[-<<+>>]>>[-<<+>>]<<]<<"
        # moving cell copy back to work
        code += "[-" + ">" * e + "+"
        code += "<" * e + "]" + ">" * e

      case "ASS":
        if self.left.token[1] == "OFF":
          if self.left.left.token[1] != "VAR":
            exit("Offset from expression failure")

          code += self.left.right.visit(brain, offset)
          code += ">"
          code += self.right.visit(brain, offset + 1)

          v = self.left.left.token[0]
          x = brain.get_var(v)
          d = brain.pointer + offset - x - 1
          e = brain.pointer + offset - x - 3
          f = brain.pointer + offset - x - 4

          # copying value for later restore
          code += "[->+>+<<]>>[-<<+>>]<<"

          # moving index and copy first
          code += "<[-" + "<" * e + "+<<+"
          code += ">" * d + "]"
          # moving set value
          code += ">[-" + "<" * f + "+"
          code += ">" * f + "]" + "<" * f + "<<<<"
          # moving the value and decreasing index
          code += "[->>>>[->>+<<]<<[->>+<<]<<[->>+<<]>>]"
          # setting value
          code += "<[-]>>>>>[-<<<<<+>>>>>]"
          # moving back somehow
          code += "<<[-<<+>>]<<[-[-<<+>>]<<]"
          # going back to work
          code += ">" * d + ">>[-<<+>>]<<"

        else:
          if self.left.token[1] != "VAR":
            exit("Assign to expression failure")
          v = self.left.token[0]
          if not brain.has_var(v):
            brain.new_var(v)
          code += self.right.visit(brain, offset)
          x = brain.get_var(v)
          d = brain.pointer + offset - x
          code += "<" * d + "[-]" + ">" * d
          code += "[->+<]>[-<+"
          code += "<" * d + "+" + ">" * (d + 1)
          code += "]<"

    return code

class Value:
  def __init__(self, token):
    self.token = token

  def __repr__(self):
    return self.token[0]

  def visit(self, brain, offset):
    code = ""
    if self.token[1] == "NUM":
      code += effective.number(int(self.token[0]))
    elif self.token[1] == "VAR":
      v = brain.get_var(self.token[0])
      d = brain.pointer + offset - v
      code += "<" * d + "[->+" + ">" * (d - 1) + "+"
      code += "<" * d + "]>[-<+>]" + ">" * (d - 1)
    return code

def compile(code, brain, offset):
  l = lexer(code)
  p = Parser(l)
  t = p.parse()

  bf = t.visit(brain, offset)

  return bf
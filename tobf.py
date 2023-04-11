# simple brainfuck language
# uses internal switches for holding places of variables
#
# should support multiple stacks upon each-other,
# so that bodies and variable privacy can exist
# therefore need to invent super memory layout
#
# empty:
# 0 -1 0000000
#
# new scope:
# 0 -1 [0 -1] (000...)
#
# new variable
# 0 -1 [a 0] 0 -1 (000...)
#
# new scope:
# 0 -1 a 0 0 -1 [0 -1] (000...)
#
# new var in new scope:
# 0 -1 a 0 0 -1 [b 0] 0 -1 (000...)
#
# one more var:
# 0 -1 a 0 0 -1 b 0 [c 0] 0 -1 (000...)
#
# pointer on last (-1)
#

import re
import effective
import parse
from sys import argv

if len(argv) < 2:
  raise Exception("No file specified")

class Brain:
  def __init__(self):
    self.scopes = []
    self.code = ">-"
    self.pointer = 1

    self.new_scope()

    self.sc = []

    self.macros = { }
    self.macro = None
    self.mcount = 0

  def new_scope(self):
    self.scopes.append(Scope(self.pointer + 1))
    self.code += ">>-"
    self.pointer += 2

  def del_scope(self):
    self.scopes.pop()
    self.code += "+<<+[-<[-]<+]-"
    if self.scopes:
      s = self.scopes[-1]
      self.pointer = s.offset
      self.pointer += s.pointer + 1
    else:
      self.pointer = 2

  def destroy(self):
    for i in range(len(self.scopes)):
      self.del_scope()

  def get_var(self, var):
    for scope in self.scopes[:: -1]:
      if scope.has_var(var):
        return scope.offset + scope.get_var(var)
    raise Exception("Var not found", var)

  def has_var(self, var):
    for scope in self.scopes[:: -1]:
      if scope.has_var(var): return True
    return False

  def new_var(self, var):
    self.scopes[-1].new_var(var)
    self.code += "+>>-"
    self.pointer += 2

  def get_macro(self, var):
    if var in self.macros:
      return self.macros[var]
    raise Exception("Macro not found")

  def execute(self, line):
    if line[0] == "#": return

    command, *arg = line.split(" ", 1)
    command, arg = command[1:], "".join(arg)

    if self.macro is not None:

      if command == "macro": self.mcount += 1
      elif command == "end": self.mcount -= 1
      if self.mcount == 0:
        self.macro = None
      else:
        self.macros[self.macro].append(line)
      return

    if line[0] == "!":

      if command == "print":

        s = "\"(?:[^\"\\\\]|\\\\.)*\""
        r = re.match(s, arg)
        if r:
          self.code += ">" + effective.string(eval(r[0])) + "<"
        else:
          self.code += ">"
          self.code += parse.compile(arg, self, 1)
          self.code += ">>+>+<[>[-<-<<[->+>+<<]>[-<+>]>>]"
          self.code += "++++++++++>[-]+>[-]>[-]>[-]<<<<<[->-[>+>>]>"
          self.code += "[[-<+>]+>+>>]<<<<<]>>-[-<<+>>]<[-]++++++++"
          self.code += "[-<++++++>]>>[-<<+>>]<<]<[.[-]<]<"
          self.code += "[-]<"

      elif command == "printr":

        self.code += ">"
        self.code += parse.compile(arg, self, 1)
        self.code += ".[-]<"

      elif command == "debug":
        self.code += "@"

      elif command == "while":
        c = parse.compile(arg, self, 1)
        self.code += ">" + c + "[[-]<"
        self.new_scope()
        self.sc.append(c)

      elif command == "done":
        c = self.sc.pop()
        self.del_scope()
        self.code += ">" + c + "]<"

      elif command == "if":
        c = parse.compile(arg, self, 1)
        self.code += ">" + c + "[[-]<"
        self.new_scope()

      elif command == "else":
        self.del_scope()
        self.code += ">>+<[-]]+>[<->-]<[[-]<"
        self.new_scope()

      elif command == "fi":
        self.del_scope()
        self.code += ">[-]]<"

      elif command == "ifnot":
        c = parse.compile(arg, self, 2)
        self.code += ">>" + c + "<+>[<->[-]]<[[-]<"
        self.new_scope()

      elif command == "read":
        v = arg.split(" ", 1)[0]
        if not v.isidentifier:
          raise Exception("Why the hell not identifier?")
        if not self.has_var(v):
          self.new_var(v)
        p = self.get_var(v)
        d = self.pointer - p
        self.code += "<" * d + "," + ">" * d

      elif command == "readi":
        v = arg.split(" ", 1)[0]
        if not v.isidentifier:
          raise Exception("Why the hell not identifier?")
        if not self.has_var(v):
          self.new_var(v)
        p = self.get_var(v)
        d = self.pointer + 1 - p

        self.code += ">"
        self.code += ">>,[>-[-----<->]"
        self.code += "<+++<<[->++++++++++<]>"
        self.code += "[-<+>]>[-<<+>>],]<<"

        self.code += "[-" + "<" * d
        self.code += "+" + ">" * d + "]<"

      elif command == "new":
        v = arg.split(" ", 1)[0]
        if not v.isidentifier:
          raise Exception("Why the hell not identifier?")
        self.new_var(v)

      elif command == "list":
        v = arg.split(" ", 1)[0]
        if not v.isidentifier:
          raise Exception("Why the hell not identifier?")
        l = int(arg.split(" ", 2)[1])
        if not 1 <= l <= 255:
          raise Exception(f"Wrong list length: {l}")
        self.new_var(v)
        self.scopes[-1].pointer += 2 * (l + 1)
        # array finishes by having two empty cells
        # but one space is already made by new_var
        self.code += "+" + ">>" * (l + 1) + "-"
        self.pointer += 2 * (l + 1)

      elif command == "macro":
        name = arg.split(" ", 1)[0]
        if not name.isidentifier:
          raise Exception("Why the hell not identifier?")
        self.macro = name
        self.mcount += 1
        self.macros[name] = []

      elif command == "!":
        name = arg.split(" ", 1)[0]
        if not name.isidentifier:
          raise Exception("Why the hell not identifier?")
        macro = self.get_macro(name)
        for line in macro:
          self.execute(line)

      else:
        raise Exception("Wrong command bre: " + command)

    else:
      c = parse.compile(line, self, 1)
      self.code += ">" + c + "[-]<"

class Scope:
  def __init__(self, offset):
    self.offset = offset
    self.pointer = 0
    self.vars = { }

  def get_var(self, var):
    return self.vars[var]

  def has_var(self, var):
    return var in self.vars

  def new_var(self, var):
    if self.has_var(var): raise Exception("Already defined var: " + var)
    self.vars[var] = self.pointer
    self.pointer += 2

code = []
def make(file):
  with open(file, "r") as file:
    c = [i.strip() for i in file.readlines() if i.strip()]
  modules = True
  for line in c:
    if line[0] == "$":
      if not modules:
        raise Exception("Modules should be imported on top!")
      make("./lib/" + line[1:] + ".lib.tobf")
    else:
      code.append(line)
      modules = False
make(argv[1])

bf = Brain()

for line in code:
  bf.execute(line)

#bf.execute("!call main ()")
bf.destroy()

head = "[Custom tobf compiler by gXLg]\n"

code = bf.code
clean = effective.clean(code)

print(head + clean)

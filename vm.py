# https://challenge.synacor.com/

import numpy as np
import sys

## OPCODES
HALT = 0   # stop       - execution and terminate the program
SET = 1    # set a b    - set register <a> to value of <b>
PUSH = 2   # push a     - push <a> onto the stack
POP = 3    # pop a      - remove the top element from the stack and write it into <a>; empty stack = error
EQ = 4     # eq a b c   - set <a> to 1 if <b> is equal to <c>; set it to 0 otherwise
GT = 5     # gt a b c   - set <a> to 1 if <b> is greater than <c>; set it to 0 otherwise
JMP = 6    # jmp a      - Jump to <a>
JT = 7     # jt a b     - if <a> is nonzero, jump to <b>
JF = 8     # jf a b     - if <a> is zero, jump to <b>
ADD = 9    # add a b c  - store into <a> the sum of <b> and <c> (modulo 32768)
MULT = 10  # mult a b c - store into <a> the product of <b> and <c> (modulo 32768)
MOD = 11   # mod a b c  - store into <a> the remainder of <b> divided by <c>
AND = 12   # and a b c  - store into <a> the bitwise AND of <b> and <c>
OR = 13    # or a b c   - store into <a> the bitwise OR of <b> and <c>
NOT = 14   # not a b    - store into <a> 15-bit bitwise inverse of <b>
RMEM = 15  # rmem a b   - read memory at address <b> and write it to <a>
WMEM = 16  # wmem a b   - write the value from <b> into memory at address <a>
CALL = 17  # call a     - write the address of the next instruction to the stack and jump to <a>
RET = 18   # ret        - remove the top element from the stack and jump to it; empty stack = halt
OUT = 19   # out a      - write the character represented by asci code <a> to the terminal
IN = 20    # in a       - read a character from the terminal and write its ascii code to <a>; assume continues till
           #              newline
NOOP = 21  # noop       - no operation

NARGS = {
    HALT: 0,
    SET: 2,
    PUSH: 1,
    POP: 1,
    EQ: 3,
    JMP: 1,
    JT: 2,
    JF: 2,
    ADD: 3,
    MULT: 3,
    MOD: 3,
    AND: 3,
    OR: 3,
    NOT: 3,
    RMEM: 2,
    WMEM: 2,
    CALL: 1,
    RET: 0,
    OUT: 1,
    IN: 1,
    NOOP: 0
}

class vm(object):
    register = np.zeros(8, dtype=np.uint16)
    memory = np.zeros(2**16, dtype=np.uint16)
    stack = []
    location = 0
    running = False
    output = ""
    old_output = ""
    test = 0
    debug = False
    input = ""


    nargs = {0: 0, 1: 2}

    def load(self, fname):
        with open(fname, "r") as f:
            self.memory = np.fromfile(f, dtype=np.uint16)
            self.location = 0

    def safeState(self, fname):
        with open(fname, "w") as f:
            np.uint16(self.location).tofile(f)
            np.uint16(len(self.stack)).tofile(f)
            np.array(self.stack, dtype=np.uint16).tofile(f)
            self.register.tofile(f)
            self.memory.tofile(f)

    def loadState(self, fname):
        with open(fname, "r") as f:
            self.location = np.fromfile(f, dtype=np.uint16, count=1)[0]
            nstack        = np.fromfile(f, dtype=np.uint16, count=1)[0]
            self.stack    = list(np.fromfile(f, dtype=np.uint16, count=nstack))
            self.register = np.fromfile(f, dtype=np.uint16, count=8)
            self.memory   = np.fromfile(f, dtype=np.uint16)


    def execute(self):
        i = self.location
        try:
            {
                HALT: self.halt,
                SET : self.set,
                PUSH: self.push,
                POP : self.pop,
                EQ  : self.eq,
                GT  : self.gt,
                JMP : self.jmp,
                JT  : self.jt,
                JF  : self.jf,
                ADD : self.add,
                MULT: self.mult,
                MOD : self.mod,
                AND : self.And,
                OR  : self.Or,
                NOT : self.Not,
                RMEM: self.rmem,
                WMEM: self.wmem,
                CALL: self.call,
                RET : self.ret,
                OUT : self.out,
                IN  : self.In,
                NOOP: self.noop,
            }[self.memory[i]]()
        except KeyError:
            print "Unknown Opcode: %d" % i
            print self.memory[i]
            self.running = False

    def run(self, location = 0):
        self.running = True
        self.location = location
        while self.running:
            self.execute()
            #print self.location

    def next(self):
        self.location += 1

    def resolve(self, i):
        if i >= 32776:
            raise ValueError("cannot resolve")
        if i >= 32768:
            return self.register[i - 32768]
        return i

    def get(self):
        self.next()
        val = self.resolve(self.memory[self.location])
        return val

    def getRegister(self):
        self.next()
        reg = self.memory[self.location] - 32768
        if reg < 0 or reg > 7:
            print "!", reg
            raise ValueError("illegal register")
        return reg

    def getTriple(self):
        return self.getRegister(), self.get(), self.get()

    def halt(self):
        print "halt encountered at location: ", self.location
        loc = self.location
        print "memory: ", self.memory[loc-32: loc+1]
        self.running = False

    def set(self):
        r = self.getRegister()
        self.register[r] = self.get()
        if (self.debug):
            print "set\t", self.location, r, self.register[r]
        self.next()

    def push(self):
        self.stack.append(self.get())
        if (self.debug):
            print "push\t", self.location, self.stack[-1]
        self.next()

    def pop(self):
        if len(self.stack) < 1:
            raise BufferError("stack underflow")
        r = self.getRegister()
        self.register[r] = self.stack.pop()
        if (self.debug):
            print "pop\t", self.location, r, self.register[r]
        self.next()

    def eq(self):
        r, a, b = self.getTriple()
        if a == b:
            self.register[r] = 1
        else:
            self.register[r] = 0
        if (self.debug):
            print "eq\t", self.location, r, a, b
        self.next()

    def gt(self):
        r, a, b = self.getTriple()
        if a > b:
            self.register[r] = 1
        else:
            self.register[r] = 0
        if (self.debug):
            print "gt\t", self.location, r, a, b
        self.next()

    def jmp(self):
        loc = self.get()
        if (self.debug):
            print "jmp\t", self.location, loc
        self.location = loc

    def jt(self):
        cond = self.get()
        loc = self.get()
        if (self.debug):
            print "jt\t", self.location, cond, loc
        if cond != 0:
            self.location = loc
        else:
            self.next()

    def jf(self):
        cond = self.get()
        loc = self.get()
        if (self.debug):
            print "jf\t", self.location, cond, loc
        if cond == 0:
            self.location = loc
        else:
            self.next()

    def add(self):
        r, a, b = self.getTriple()
        self.register[r] = (a + b) % 32768
        if (self.debug):
            print "add\t", self.location, r, a, b, self.register[r]
        self.next()

    def mult(self):
        r, a, b = self.getTriple()
        d = np.int32(a)
        d = (d * b) % 32768
        self.register[r] = d
        if (self.debug):
            print "mult\t", self.location, r, a, b, self.register[r]
        self.next()

    def mod(self):
        r, a, b = self.getTriple()
        self.register[r] = (a % b)
        if (self.debug):
            print "mod\t", self.location, r, a, b, self.register[r]
        self.next()

    def And(self):
        r, a, b = self.getTriple()
        self.register[r] = (a & b)
        if (self.debug):
            print "and\t", self.location, r, a, b, self.register[r]
        self.next()

    def Or(self):
        r, a, b = self.getTriple()
        self.register[r] = (a | b)
        if (self.debug):
            print "or\t", self.location, r, a, b, self.register[r]
        self.next()

    def Not(self):
        r = self.getRegister()
        a = self.get()
        self.register[r] = a ^ ((1<<15) - 1)
        if (self.debug):
            print "not\t", self.location, r, a, self.register[r]
        self.next()

    def rmem(self):
        r = self.getRegister()
        self.register[r] = self.memory[self.get()]
        if (self.debug):
            print "rmem\t", self.location, r, self.register[r]
        self.next()

    def wmem(self):
        address = self.get()
        val     = self.get()
        self.memory[address] = val
        if (self.debug):
            print "wmem\t", self.location, address, val
        self.next()

    def call(self):
        loc = self.get()
        self.stack.append(self.location + 1)
        if (self.debug):
            print "call\t", self.location, loc
        self.location = loc

    def ret(self):
        if len(self.stack) < 1:
            raise BufferError("empty stack")
        self.location = self.stack.pop()
        if (self.debug):
            print "ret\t", self.location

    def out(self):
        self.output += chr(self.get())
        if (self.debug):
            print "out\t", self.location, self.output[-1]
        if self.output[-1] == "\n":
            if self.output[:1] == "s":
                # self.safeState('memdump')
                print self.location
                print self.register
                print self.stack
            print self.output
            self.output = ""
        self.next()

    def In(self):
        r = self.getRegister()
        if (self.debug):
            print "in\t", self.location, r
        # self.debug = True
        if len(self.input) < 1:
            self.input = raw_input("> ")
            self.input += "\n"
        self.register[r] = ord(self.input[0])
        self.input = self.input[1:]
        self.next()

    def noop(self):
        if (self.debug):
            print "noop\t", self.location
        self.next()

VM = vm()
VM.debug = False
# VM.load('challenge.bin')
VM.loadState('memdump')
VM.next()

print VM.location
print VM.register
print VM.stack
try:
    VM.run(VM.location)
except ValueError:
    loc = VM.location
    print "memory:   ", VM.memory[loc-1:loc+3]
    print "register: ", VM.register
    raise

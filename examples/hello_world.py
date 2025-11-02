import dt31.instructions as I
from dt31.cpu import DT31
from dt31.operands import L, M

hello_world = [
    # populate stack with hello world backwards
    I.PUSH(33),
    I.PUSH(100),
    I.PUSH(108),
    I.PUSH(114),
    I.PUSH(111),
    I.PUSH(119),
    I.PUSH(32),
    I.PUSH(44),
    I.PUSH(111),
    I.PUSH(108),
    I.PUSH(108),
    I.PUSH(101),
    I.PUSH(104),
    # Pop off the stack into M[1]
    I.POP(M[1]),
    # If stack is empty, set M[2] = 1, else 0
    I.SEMP(M[2]),
    # Print M[1]; add a newline if M[2] == 1 (i.e. if stack is empty)
    I.OOUT(M[1], M[2]),
    # if M[2] is 0 (i.e. stack is not empty), loop back
    I.RJEQ(L[-3], M[2], 0),
]

cpu = DT31(registers=[])
cpu.run(hello_world, debug=True)

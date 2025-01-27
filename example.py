import dt31.instructions as I
from dt31.cpu import DT31
from dt31.operands import L, M

hello_world = [
    I.PUSH(33),  # populate stack with hello world backwards
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
    I.POP(M[1]),
    I.SEMP(M[2]),  # M[2] = 0 if stack is empty, else 1
    I.OOUT(M[1], M[2]),  # add newline if M[2] == 1
    I.RJEQ(-3, M[2], 0),  # if M[2] is 0, loop
]

cpu = DT31(registers=[])
cpu.run(hello_world)

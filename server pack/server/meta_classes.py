import dis


class ServerMaker(type):
    def __init__(self, clsname, bases, clsdict):
        methods = []
        attrs = []

        for func in clsdict:
            try:
                instr_iter = dis.get_instructions(clsdict[func])
            except TypeError:
                pass
            else:
                for instr in instr_iter:
                    print(instr)
                    if instr.opname == 'LOAD_GLOBAL':
                        if instr.argval not in methods:
                            methods.append(instr.argval)
                    elif instr.opname == 'LOAD_ATTR':
                        if instr.argval not in attrs:
                            attrs.append(instr.argval)
        print(methods)

        if 'connect' in methods:
            raise TypeError('Использование метода connect недопустимо в серверном классе')

        if not ('SOCK_STREAM' in attrs and 'AF_INET' in attrs):
            raise TypeError('Некорректная инициализация сокета.')
        super().__init__(clsname, bases, clsdict)


class ClientMaker(type):
    def __init__(self, clsname, bases, clsdict):
        methods = []

        for func in clsdict:
            try:
                instr_iter = dis.get_instructions(clsdict[func])
            except TypeError:
                pass
            else:
                for instr in instr_iter:
                    if instr.opname == 'LOAD_GLOBAL':
                        if instr.argval not in methods:
                            methods.append(instr.argval)

        for command in ('accept', 'listen', 'socket'):
            if command in methods:
                raise TypeError('В классе обнаружено использование запрещённого метода')
        super().__init__(clsname, bases, clsdict)

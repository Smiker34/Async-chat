data = 'сетевое программирование\nсокет\nдекоратор'

with open('test_file.txt', 'w') as f:
    f.write(data)
    print(f.encoding)


with open('test_file.txt', 'r', encoding='utf-8') as f:  # UnicodeDecodeError: 'utf-8' codec can't decode byte 0xf1 in position 0: invalid continuation byte
    print(f.read())

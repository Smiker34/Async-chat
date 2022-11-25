print('разработка'.encode())  # b'\xd1\x80\xd0\xb0\xd0\xb7\xd1\x80\xd0\xb0\xd0\xb1\xd0\xbe\xd1\x82\xd0\xba\xd0\xb0'
print('разработка'.encode().decode())  # разработка

print('администрирование'.encode())  # b'\xd0\xb0\xd0\xb4\xd0\xbc\xd0\xb8\xd0\xbd\xd0\xb8\xd1\x81\xd1\x82\xd1\x80\xd0\xb8\xd1\x80\xd0\xbe\xd0\xb2\xd0\xb0\xd0\xbd\xd0\xb8\xd0\xb5'
print('администрирование'.encode().decode())  # администрирование

print('protocol'.encode())  # b'protocol'
print('protocol'.encode().decode())  # protocol

print('standard'.encode())  # b'standard'
print('standard'.encode().decode())  # standard

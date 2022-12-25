import subprocess

processes = []

while True:
    try:
        client_num = int(input('Введите число пользователей: '))
        break
    except ValueError:
        print("Введено не число")

processes.append(subprocess.Popen('python server.py', creationflags=subprocess.CREATE_NEW_CONSOLE))

for i in range(client_num):
    processes.append(subprocess.Popen(f'python read-write_client.py -n test{i+1}',
                                      creationflags=subprocess.CREATE_NEW_CONSOLE))

exit = input("Введите что-нибудь для выхода: ")
while processes:
    processes.pop().kill()

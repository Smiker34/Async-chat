import subprocess

pings = [['ping', 'yandex.ru'], ['ping', 'youtube.com']]

for ping_now in pings:

    ping_process = subprocess.Popen(ping_now, stdout=subprocess.PIPE)

    i = 0

    for line in ping_process.stdout:
        if i <= 10:
            print(line)
            print(line.decode('cp866').encode('utf-8').decode('utf-8'))
            i += 1
        else:
            print('#' * 30)
            break

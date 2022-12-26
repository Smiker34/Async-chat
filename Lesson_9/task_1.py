from ipaddress import ip_address
from subprocess import Popen, PIPE


def host_ping(list_ip_addresses, timeout=500, requests=1):
    result = {"Доступные узлы": '', "Недоступные узлы": ''}
    for address in list_ip_addresses:
        try:
            address = ip_address(address)
        except ValueError:
            pass

        proc = Popen(f"ping {address} -w {timeout} -n {requests}", shell=False, stdout=PIPE)
        proc.wait()
        if proc.returncode == 0:
            print(f'{address} - Узел доступен')
            result["Доступные узлы"] += f'{str(address)}\n'
        else:
            print(f'{address} - Узел недоступен')
            result["Недоступные узлы"] += f'{str(address)}\n'
    return result


if __name__ == '__main__':
    ip_addresses = ['yandex.ru', 'google.com', '192.168.0.1', '192.168.0.101']
    host_ping(ip_addresses)

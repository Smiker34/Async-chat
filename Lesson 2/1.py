import re
import csv


def get_data(files_count):
    names = []
    products = []
    codes = []
    types = []
    for idx in range(files_count):
        try:
            with open('info_' + str(idx + 1) + '.txt') as f:
                for line in f.readlines():
                    if re.match(r'Название ОС', line):
                        names.append(line[line.index(':')+1:line.index('\n')].strip())
                    elif re.match(r'Изготовитель ОС', line):
                        products.append(line[line.index(':')+1:line.index('\n')].strip())
                    elif re.match(r'Код продукта', line):
                        codes.append(line[line.index(':')+1:line.index('\n')].strip())
                    elif re.match(r'Тип системы', line):
                        types.append(line[line.index(':')+1:line.index('\n')].strip())
                    else:
                        continue
        except FileNotFoundError:
            break

    data = [['Название системы', 'Изготовитель системы', 'Код продукта', 'Тип системы']]
    for idx in range(len(names)):
        data.append([names[idx], products[idx], codes[idx], types[idx]])

    return data


def write_to_csv(link, file_count):
    data = get_data(file_count)
    with open(link, 'w') as f:
        for row in data:
            csv.writer(f).writerow(row)


write_to_csv('data.csv', 3)

with open('data.csv', 'r') as f:
    print(f.read())

import yaml


data = {
    '1€': ['Some', 'text'],
    '2€': 52,
    '3€': {'Some': 'text'}
}

with open('file.yaml', 'w') as f:
    yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

with open('file.yaml') as f:
    yaml_data = yaml.full_load(f)
    if yaml_data == data:
        print("Совпадает")
    else:
        print("Не совпадает")

import json

label = {
    'thread_size': 'M3', 'thread_pitch': '0.5mm', 'length': '6mm'
}

models = ['92095A179', '92095A181', '92095A182']

for model in models:
    with open(model + ".json", 'w') as outfile:
        json.dump(label, outfile)

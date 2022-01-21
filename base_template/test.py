with open("context.py", "r", encoding="utf-8") as file:
    a = list(filter(lambda x: '#' not in x, map(str.strip, file.readlines())))
    print(a)

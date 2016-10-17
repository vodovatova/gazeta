import os

DIR = os.path.split(os.path.abspath(__file__))[0]

s = {
    'Россия': ('Москва', 11.5),
    'Китай': ('Пекин', 11.51),
    'Бразилия': ('Бразилиа', 2.48)
}

for c in s.keys():
    if not os.path.exists("%s\\%s" % (DIR, c)):
        os.makedirs("%s\\%s" % (DIR, c))
    f = open("%s\\%s\\info.txt" % (DIR, c), 'w')
    f.write("%s, %d" % (s[c][0], s[c][1]))
    f.close()

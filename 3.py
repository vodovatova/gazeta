import crawler

c = crawler.Crawler(metadata=False)
data = c.get_data("http://www.vestnik.udm.net/?p=2151")

print(
    "Название: %s\nАвтор: %s\nДата публикации: %s\nКатегории: %s\n"
    % (data['header'], data['author'], data['date'], data['topic'])
)

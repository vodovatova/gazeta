import crawler

c = crawler.Crawler()
links = c.get_links(200)
for lnk in links:
    data = c.get_data(lnk)
    data = c.create_files(data)
    c.update_metadata(data)

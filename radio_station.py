class RadioStation:
    def __init__(self, id, category, name, url):
        self.id = id
        self.category = category
        self.name = name
        self.url = url

    @classmethod
    def fromCSV(cls, csv):
        return cls(csv[0], csv[1], csv[2], csv[3])
    
    def __str__(self):
        return 'Station[%s %s %s %s]' % (self.id, self.category, self.name, self.url)
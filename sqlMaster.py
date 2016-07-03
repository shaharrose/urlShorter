import sqlite3 as sql


class sqlMaster:
    def __init__(self):
        self.open()
        # self.cur.execute("DROP TABLE urls")
        # self.cur.execute("CREATE TABLE urls(localPath TEXT, destination TEXT)")
        self.close()
        pass

    # print cur.execute("select * from images").fetchall()

    def open(self):
        self.con = sql.connect('urls.db')
        self.cur = self.con.cursor()

    def insert(self, localPath, destination):
        self.open()
        self.cur.execute("INSERT INTO urls VALUES('%s', '%s')" % (localPath, destination))
        self.close()
        # print self.getAll()

    def getAll(self):
        self.open()
        s = self.cur.execute("SELECT * FROM urls").fetchall()
        self.close()
        l = list(s)
        x = []
        for r in l:
            x.append(list(r))
        return x

    def getAllDict(self):
        self.open()
        s = self.cur.execute("SELECT * FROM urls").fetchall()
        self.close()
        dict = {}
        for tup in s:
            dict[tup[0]] = tup[1]
        return dict

    def close(self):
        self.cur.close()
        self.con.commit()
        self.con.close()

    def hasLocalPath(self, localPath):
        data = self.getAll()
        for entry in data:
            if entry[0].encode("ascii") == localPath:
                return True
        return False

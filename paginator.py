import logging

class Paginator(object):
    def __init__(self, objects, key, letter, offset, pagesize):
        self.objects = objects
        self.letter = letter.lower()
        self.offset = offset
        self.pagesize = pagesize
        self.start = 0

        for i, v in enumerate(objects):
            try:
                # Try object style first.
                cur = getattr(v, key)[0]
            except AttributeError:
                # Now try dict.
                cur = v.get(key)
                if cur is None:
                    raise AttributeError

            cur = cur.lower()

            if cur < letter:
                self.start = i
            elif cur == letter:
                self.start = i
                break

        self.start += offset * pagesize

        if self.start < 0:
            self.start = 0
        elif self.start >= len(objects):
            self.start = len(objects) - len(objects) % pagesize

        logging.info('Letter: %s, Offset: %s, Page Size: %s, Length: %s, Start: %s', letter, offset, pagesize, len(objects), self.start)

    def page(self):
        return self.objects[self.start:self.start + self.pagesize]

import math


class Paginator(object):

    def __init__(self, data, page_size=10, page=1):
        if page < 1:
            raise IndexError('Page exceeds minimum number of pages')

        self.data = data
        self.page_size = page_size
        self.page = page
        self.total_items = len(data)
        self.num_pages = int(math.ceil(self.total_items / float(self.page_size)))

        # Slice the dataset
        start_idx = (page - 1) * page_size
        end_idx = page * page_size

        self.items = data[start_idx:end_idx]
        if not self.items and page != 1:
            raise IndexError('Page exceeds maximum number of pages')

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.num_pages

    @property
    def next_page(self):
        return self.page + 1

    @property
    def prev_page(self):
        return self.page - 1

    def pages(self, before=2, after=2):
        undershoot = self.page - before
        overshoot = self.page + after

        if undershoot < 1:
            start = 1
            end = min(self.page + after + abs(undershoot) + 1, self.num_pages)
        elif overshoot > self.num_pages:
            diff = overshoot - self.num_pages
            start = max(self.page - before - diff, 1)
            end = self.num_pages
        else:
            start = max(self.page - before, 1)
            end = min(self.page + before, self.num_pages)

        return xrange(start, end + 1)

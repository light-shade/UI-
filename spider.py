import threading
import time
from queue import Queue
from settings import MAX_PAGE, DL_PSD, FILE_DIR, MAX_QUEUE, MAX_THREAD
from httprequest import UrlHandler, Download


class Producer(threading.Thread):
    def __init__(self, queue, task,):
        threading.Thread.__init__(self)
        self.task_stop = False
        self.task = task
        self.queue = queue

    def run(self):
        tasks = self.task.get_tasks()
        while True:
            try:
                task = next(tasks)
            except StopIteration:
                break
            else:
                self.queue.put(task)

    def stop(self):
        self.task_stop = True


class Consumer(threading.Thread):
    def __init__(self, queue, donwload):
        threading.Thread.__init__(self)
        self.task_stop = False
        self.queue = queue
        self.download = donwload

    def run(self):
        while not self.task_stop:
            try:
                data_ = self.queue.get(timeout=4)
            except Exception as e:
                print(e.args)
                break
            else:
                self.download(data_, dl_dir=FILE_DIR, has_psd=DL_PSD, ).work()
                self.queue.task_done()

    def stop(self):
        self.task_stop = True


def wrapper(func, *args, **kwargs):
    def timer():
        start_time = time.time()
        func(*args, **kwargs)
        end_time = time.time()
        print('总用时:-->', int(end_time - start_time))
    return timer


@wrapper
def main():
    q = Queue(MAX_QUEUE)
    t1_thread = []
    t2_thread = []
    for url in ['http://www.uimaker.com/uimakerdown/list_36_{}.html'.format(i) for i in range(1, MAX_PAGE)]:
        t1 = Producer(q, UrlHandler(url))
        t1.start()
        t1_thread.append(t1)

    for i in range(MAX_THREAD):
        t2 = Consumer(q, Download)
        t2.start()

    for t1 in t1_thread:
        t1.join()

    for t2 in t2_thread:
        t2.join()

    q.join()


if __name__ == '__main__':
    main()

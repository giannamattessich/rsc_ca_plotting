from PyQt5.QtCore import Qt, QObject, pyqtSignal as Signal, pyqtSlot as Slot, QThreadPool
from src.workutils.WorkerThread import Worker

# # class to handle the execution of tasks in the queue sequentially-> set up finished signal
class TaskManager(QObject):
    # setup finished signal
    tasks_completed = Signal()
    task_progress = Signal()
    

# initialize queue and index of tasks
    def __init__(self, parent=None):
        super(TaskManager, self).__init__(parent)
        self.task_queue = [] # queue
        self.current_task_index = 0
        self.process_object = None
        self.is_running = False
        #self.workers = []
        
# set the type of data process object to perform on-> either timeseries or longitudinal process
    def set_process_object(self, process_object):
        self.process_object = process_object


# add the function name and optional arguments to the queue 
    def add_task(self, method_name, *args, **kwargs):
        self.task_queue.append((method_name, args, kwargs))

# start at beginning of queue and execute task
    def start_tasks(self):
        self.current_task_index = 0
        self.execute_next_task()

# for each task construct a worker object that will execute the run function
# setup finished signal (queued connection) to be emitted when worker is finished with task
# start thread from global thread pool 
# if at end of queue emit tasks_completed signal
    def execute_next_task(self):
        if self.current_task_index < len(self.task_queue):
            self.is_running = True
            method_name, args, kwargs = self.task_queue[self.current_task_index]
            worker = Worker(self.process_object, method_name, *args, **kwargs)
            worker.signals.finished.connect(self.on_task_finished, Qt.QueuedConnection)
            QThreadPool.globalInstance().start(worker)
        else:
            # All tasks completed
            self.is_running = False 
            self.tasks_completed.emit()
            self.task_queue.clear()

# hook up finished signal to slot for task and execute next task in queue
    @Slot()
    def on_task_finished(self):
        self.current_task_index += 1
        self.execute_next_task()
    
    # remove tasks in task queue to stop processing
    def quit_tasks(self):
        if self.is_running:
            self.task_queue.clear()

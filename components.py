import itertools
import pandas as pd
import numpy as np

# Build a warehouse - should have attributes for each x,y coordinate for the hallways.  Forklifts can travel solo, or wait in queues eventually
# Right now want to keep track of whether occupied or not.
class FloorPatch:
    def __init__(self):
        self.occupied = 0
        self.forklift_count = 0
        self.forklift_max = 1
    def add_forklift(self):
        self.forklift_count +=1
        if self.forklift_count >= self.forklift_max:
            self.occupied = 1
    def remove_forklift(self):
        self.forklift_count -=1
        if self.forklift_count < self.forklift_max:
            self.occupied = 0

class Warehouse:
    def __init__(self, x_dim, y_dim, receiving, shipping, lab):
        self.x_dim = x_dim
        self.y_dim = y_dim
        for element in itertools.product(range(x_dim), range(y_dim)):
            setattr(self, str(list(element)), FloorPatch())
        for element in [receiving, shipping, lab]:
            position = self.__getattribute__(str(element))
            position.forklift_max = 3


class Forklift:
    def __init__(self, start_position, job_list):
        self.position = start_position # actually the destination
        self.prev_position = start_position
        self.job_list = job_list # should be 'task' list
        self.job_number = 0
        self.next_update_time = 0
        self.status = '' #['traveling', 'waiting', 'picking', 'complete']
        #print("self.job_list", self.job_list)
        
    def update_travel_time(self, t):
        if self.job_number == len(self.job_list):
            self.status = 'complete'
        else:
            x, y = self.position
            end_x, end_y = self.job_list[self.job_number]
            self.job_number += 1
            self.next_update_time = t+ np.ceil( (abs(end_x-x) + abs(end_y - y))*np.random.normal(1, .2, 1)[0] )
            self.prev_position = self.position # update the last known location
            self.position = [end_x, end_y]
            self.status = 'traveling'

    def update_pick_up_time(self, t):
        self.next_update_time = t + np.random.choice([10,20])
        self.status = 'picking'
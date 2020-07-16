import pandas as pd
from components import Warehouse, Forklift
"""
    New features (newer things last):
    1. Added switch var output_to_csv = True to decide whether to output a csv file
    2. Added switch var if_print = True to decide whether to print running progress
    3. Added a return on each run for the time steps taken
    4. Added the last recorded location to the output data
"""
class Simulation:
    def __init__(self, warehouse_x_dim, warehouse_y_dim, receiving, shipping, lab, n_forklifts, forklift_job_lists,
                output_to_csv = True, if_print = True):
        if len(forklift_job_lists) < n_forklifts:
            raise "Need at least as many jobs as forklifts"
        self.n_forklifts = n_forklifts
        self.forklift_start_positions = [[0, 0] for k in range(n_forklifts)]
        self.n_jobs = len(forklift_job_lists)
        self.warehouse = Warehouse(warehouse_x_dim, warehouse_y_dim, receiving, shipping, lab)
        self.forklift_names=[]
        self.forklift_job_lists=forklift_job_lists
        self.output_to_csv = output_to_csv # if output a csv file. default = True
        self.if_print = if_print # if print job number completed. default = True
        for k in range(self.n_forklifts):
            self.__setattr__('Forklift'+str(k), Forklift(self.forklift_start_positions[k], forklift_job_lists[k]))
            self.forklift_names.append('Forklift'+str(k))

    def run(self, outputfile):
        output = pd.DataFrame()
        t = 0
        job_ticker = self.n_forklifts
        for name in self.forklift_names:
            forklift = self.__getattribute__(name)
            forklift.update_travel_time(t)
        while job_ticker < len(self.forklift_job_lists) + self.n_forklifts:
            for name in self.forklift_names:
                forklift = self.__getattribute__(name)
                if forklift.next_update_time <= t:
                    if (forklift.status == 'traveling') or (forklift.status == 'waiting'):
                        if self.warehouse.__getattribute__(str(forklift.position)).occupied == 0:
                            self.warehouse.__getattribute__(str(forklift.position)).add_forklift()
                            forklift.update_pick_up_time(t)
                        else:
                            forklift.status = 'waiting'
                    elif forklift.status == 'picking':
                        self.warehouse.__getattribute__(str(forklift.position)).remove_forklift()
                        forklift.update_travel_time(t)
                        if forklift.status == 'complete':
                            if self.if_print == True: # print job number completed
                                print("number",job_ticker - self.n_forklifts,"jobs completed!")
                            if job_ticker < len(self.forklift_job_lists):
                                forklift.job_list = self.forklift_job_lists[job_ticker]
                                forklift.job_number = 0
                                forklift.update_travel_time(t)
                            job_ticker += 1
                            #print("Time: ", t, " Jobs Completed: ", job_ticker - self.n_forklifts, " Total Jobs: ", len(self.forklift_job_lists))
                output = output.append([[t, 
                                         name, 
                                         forklift.position,
                                         forklift.prev_position, 
                                         forklift.status,
                                         forklift.next_update_time]])
            
            t += 1
        output.columns = ['time',
                          'name',
                          'current_destination',
                          'last_loc',
                          'status',
                          'next_update_time']
        output.to_csv(outputfile, index=False)
        print("simulation complete, total time = ",t)
        return t # return the total time spent for this run
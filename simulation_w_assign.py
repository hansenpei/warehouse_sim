import pandas as pd
from components import Warehouse, Forklift
"""
    New features (newer things last):
    1. Added switch var output_to_csv = True to decide whether to output a csv file
    2. Added switch var if_print = True to decide whether to print running progress
    3. Added a return on each run for the time steps taken
    4. Added the last recorded location to the output data
    5. Added a job assignment list argument: e.g. [[4,8],[3,9,0]...] means FL0 does job 4 and 8, etc.
    Has the length of n_forklifts.
"""
class Simulation:
    def __init__(self, warehouse_x_dim, warehouse_y_dim, 
                 receiving, shipping, lab, n_forklifts, 
                 forklift_job_lists, job_assign_list = None, # dummy value here
                output_to_csv = False, if_print = False):
        if len(forklift_job_lists) < n_forklifts:
            raise "Need at least as many jobs as forklifts"
        self.n_forklifts = n_forklifts
        self.forklift_start_positions = [[0, 0] for k in range(n_forklifts)]
        self.n_jobs = len(forklift_job_lists)
        self.warehouse = Warehouse(warehouse_x_dim, warehouse_y_dim, receiving, shipping, lab)
        self.forklift_names=[]
        self.forklift_job_lists=forklift_job_lists
        self.job_assign_list = job_assign_list # [0]*len(forklift_job_lists) 
        self.output_to_csv = output_to_csv # if output a csv file. default = True
        self.if_print = if_print # if print job number completed. default = True
        self.job_dict = self._make_job_dict()
        self._init_forklifts()
    
    def _assign_job(self,_forklift_name):
        """
        Assigns a specific forklift a specific job, and updates the available job dictionary: self.job_dict
        Input: forklift's name
        Output: the index of the next job
        """
        fl_name = _forklift_name # a string, e.g. 'Forklift3'
        if self.job_dict[fl_name] == []: # if there's no more job left for this forklift
            next_job_index = None # return None
        else:
            next_job_index = self.job_dict[fl_name][0] # assign the next job
            del self.job_dict[fl_name][0] # delete the job that is just assigned
        return next_job_index
    
    def _init_forklifts(self):
        """
        Initialize forklift names, their starting positions, and their first job
        """
        for k in range(self.n_forklifts):
            job_first_occurr = self.job_dict['Forklift'+str(k)][0]
            del self.job_dict['Forklift'+str(k)][0] # delete the job that is just assigned
            self.__setattr__('Forklift'+str(k), Forklift(self.forklift_start_positions[k], 
                                                         self.forklift_job_lists[job_first_occurr]))
            self.forklift_names.append('Forklift'+str(k))
            #print("Forklift", k, "is doing job",self.forklift_job_lists[job_first_occurr])
        
    def _make_job_dict(self):
        """
        Makes a dictionary specifying which forklift should do which jobs
        key: forklift name, e.g. "Forklift0" etc
        values: forklift jobs that have not done, e.g. [1,0,8]
        """
        forklift_job_dict = {}
        for index, job in enumerate(self.job_assign_list):
            forklift_job_dict['Forklift'+str(index)] = job
        return forklift_job_dict
        
        
    def run(self, outputfile = None):
        output = pd.DataFrame()
        t = 0
        job_ticker = self.n_forklifts # the last job that has been assigned
        #job_done = self.n_forklifts
        for name in self.forklift_names:
            forklift = self.__getattribute__(name)
            forklift.update_travel_time(t)
        #time_end = {name: False for name in self.forklift_names} # whether the current time is no less than the next update times
        #terminate = sum(time_end.values())
        while job_ticker < len(self.forklift_job_lists) + self.n_forklifts: 
            
            for name in self.forklift_names:
                forklift = self.__getattribute__(name)
                if forklift.next_update_time <= t:
                    #time_end[name] = F
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
                            #job_done += 1
                            if self.if_print == True: # print job number completed
                                print("number of ",job_ticker,"jobs completed!")
                            if True:#job_ticker < len(self.forklift_job_lists):
                                job_index = self._assign_job(name) #
                                if job_index == None:
                                    forklift.update_travel_time(t) 
                                else:
                                    #print("job_index", job_index, "job_done", job_ticker - self.n_forklifts + 1)
                                    #job_ticker += 1
                                    forklift.job_list = self.forklift_job_lists[job_index] #
                                    #print(name, "starts doing", job_index)
                                    forklift.job_number = 0
                                    forklift.update_travel_time(t)
                                    
                            print("job_ticker now", job_ticker)
                            #print("job_done now", job_done)
                            #print("job dict", self.job_dict)
                            job_ticker += 1
                ###############################################################                                       
                # Output part. This part is slow due to storing data. 
                if self.output_to_csv == True:
                    output = output.append([[t, 
                                             name, 
                                             forklift.position,
                                             forklift.prev_position, 
                                             forklift.status,
                                             forklift.next_update_time]])

            t += 1 # for name in self.forklift_names:
            #terminate = sum(time_end.values())
            #print('terminate', terminate)
            #for value in time_end.values():
                
        if self.output_to_csv == True:
            output.columns = ['time',
                              'name',
                              'current_destination',
                              'last_loc',
                              'status',
                              'next_update_time']
            output.to_csv(outputfile, index=False)
        #print("job_ticker is", job_ticker)
        #print("simulation complete, total time = ",t)
        return t # return the total time spent for this run
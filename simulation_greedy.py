import pandas as pd
from components import Warehouse, Forklift
from greedy_engine_naive import Greedy_engine_naive
"""
    New features (newer things last):
    1. Added switch var output_to_csv = True to decide whether to output a csv file
    2. Added switch var if_print = True to decide whether to print running progress
    3. Added a return on each run for the time steps taken
    4. Added the last recorded location to the output data
    5. Uses a greedy engine to assign the next job
"""
class Simulation:
    def __init__(self, warehouse_x_dim, warehouse_y_dim, 
                 receiving, shipping, lab, n_forklifts, 
                 forklift_job_lists, job_assign_list = None, # dummy value here
                output_to_csv = True, if_print = True):
        if len(forklift_job_lists) < n_forklifts:
            raise "Need at least as many jobs as forklifts"
        self.n_forklifts = n_forklifts
        self.forklift_start_positions = [[0, 0] for k in range(n_forklifts)]
        self.n_jobs = len(forklift_job_lists)
        self.warehouse = Warehouse(warehouse_x_dim, warehouse_y_dim, receiving, shipping, lab)
        self.forklift_names=[]
        self.forklift_job_lists=forklift_job_lists
        self.job_assign_list =  list(range(len(forklift_job_lists))) #job_assign_list
        self.output_to_csv = output_to_csv # if output a csv file. default = True
        self.if_print = if_print # if print job number completed. default = True
        self.job_avai_bl = [True for i in range(self.n_jobs)] # everywork is available in the beginning
        
        # create a job assigning engine: Greedy_engine
        self.JAE = Greedy_engine_naive(warehouse_dim = warehouse_x_dim, 
                                                 n_forklifts = self.n_forklifts,
                                                 receiving = receiving,
                                                 shipping = shipping,
                                                 lab = lab,
                                                 job_list = self.forklift_job_lists,
                                                 weight = 1)

        for k in range(self.n_forklifts):
            job_first_occurr = self.job_assign_list.index(k)
            self.__setattr__('Forklift'+str(k), Forklift(self.forklift_start_positions[k], 
                                                         self.forklift_job_lists[job_first_occurr]))
            self.forklift_names.append('Forklift'+str(k))
            self.job_avai_bl[k] = False

            #print("Forklift", k, "is doing job",forklift_job_lists[job_first_occurr])
    # function that takes in forklift name, and job_ticker, returns the next job(in terms of index)
    # that the fork_lift should do.
    def assign_job(self,_forklift_name, _n_job_done):
        _forklift_name = int((_forklift_name[8:])) # 8 is the length of "Forklift". Error prone hard coding. 
        leftover_job_assign = self.job_assign_list[(_n_job_done):] # _n_job_done takes value from 1,2,3,...
        #print("leftover = ", leftover_job_assign)
        try:
            next_job_index = leftover_job_assign.index(_forklift_name) + _n_job_done
        except:
            next_job_index = None
        return next_job_index
        
    """
    outlet: next job's index, which is the closest
    
    goal: pick the next job that is the closest 
    """
        
    def run(self, outputfile):
        output = pd.DataFrame()
        t = 0
        job_ticker = self.n_forklifts # the last job that has been assigned 
        for name in self.forklift_names: # initial updates
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
                                print("number of ",job_ticker - self.n_forklifts + 1,"jobs completed!")
                            if (job_ticker - self.n_forklifts + 1) < len(self.forklift_job_lists): # still job available
                                [job_index, self.job_avai_bl] = self.JAE.next_job_index(_current_pos = forklift.position,
                                                                _job_avai_bl = self.job_avai_bl) #
                                #print('t, forklift.next_update_time, forklift.status',
                                      #t, forklift.next_update_time, forklift.status)
                                if job_index == None:
                                    #job_ticker += 1
                                    forklift.job_number = 0
                                    #forklift.update_travel_time(t)
                                    #continue
                                else:
                                    #print("job_index", job_index, "job_done", job_ticker - self.n_forklifts + 1)
                                    forklift.job_list = self.forklift_job_lists[job_index] #
                                    #print(name, "currently doing", forklift.job_list)
                                    forklift.job_number = 0
                                    
                                    forklift.update_travel_time(t)
                            #print("job_ticker now", job_ticker)
                            #print("forklift info", name)
                            job_ticker += 1
                            #print("Time: ", t, " Jobs Completed: ", job_ticker - self.n_forklifts, " Total Jobs: ", len(self.forklift_job_lists))
                            
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
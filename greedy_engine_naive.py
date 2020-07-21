import numpy as np
import copy
class Greedy_engine_naive:
    def __init__(self, warehouse_dim, n_forklifts, receiving, shipping, lab, job_list, weight):
        self.warehouse_dim = warehouse_dim
        self.n_forklifts = n_forklifts
        self.receiving = receiving
        self.shipping = shipping
        self.lab = lab
        self.job_list = job_list
        self.weight = weight
        self.n_jobs = len(job_list)
        
    def next_job_index(self, _current_pos ,_job_avai_bl):
        """
          returns the next job's index which is the closest 
        """
        if sum(_job_avai_bl) == 0: # if it is all false, i.e., no job available
            return [None, _job_avai_bl]
        # 0. initiation
        all_jobs = self.job_list
        current_pos = _current_pos
        job_avai_bl = _job_avai_bl
        # 1. compose a list of available jobs now
        # index of available jobs in terms of all jobs
        avai_index = [i for i, x in enumerate(_job_avai_bl) if x==True] 
        avai_jobs = [all_jobs[i] for i in avai_index]
        # 2. find the job that is the closest in the available jobs
        distance_data = [10000000]*len(avai_jobs)
        #print('avai jobs', avai_jobs)
        for i, job in enumerate(avai_jobs):
            #print("job",job)
            distance_data[i] = abs(current_pos[0]-job[0][0]) + abs(current_pos[1]-job[0][1])
        #print('distance_data', distance_data)
        min_dis = min(distance_data)
        index_in_avai = distance_data.index(min_dis)
        # 3. return the index for the next job in terms of the the full job list
        index_for_next_job = avai_index[index_in_avai]
        # 4. return the boolean list updated
        job_avai_bl[index_for_next_job] = False
        #print("index_for_next_job",index_for_next_job)
        return [index_for_next_job, job_avai_bl]


class Reorder_engine:
    def __init__(self, warehouse_dim, n_forklifts, receiving, shipping, lab, job_list, weight):
        self.warehouse_dim = warehouse_dim
        self.n_forklifts = n_forklifts
        self.receiving = receiving
        self.shipping = shipping
        self.lab = lab
        self.job_list = job_list
        self.weight = weight
        self.n_jobs = len(job_list)

    def length_job(self, job):
        """
        find distance of job
        """
        N_TASKS = len(job)-1 #number of tasks
        this_dist = 0 #the distance for this permutation
        for j in range(0,N_TASKS):
            this_dist += abs(job[j][0]-job[j+1][0]) + abs(job[j][1]-job[j+1][1]) #add distance between tasks
        return this_dist

    def order_runs(self):
        """
        job_list should be in np.array format to work correctly

        N_FORKLIFTS is number of forklifts

        WAREHOUSE_DIM is dimension of warehouse

        weight = 1 means forklifts don't care about their 'preference'
        weight = 0.00000001 means the forklift will only do jobs within their 'preference'

        """
        job_list = self.job_list
        N_FORKLIFTS = self.n_forklifts
        WAREHOUSE_DIM = self.warehouse_dim
        weight = self.weight

        N_JOBS = len(self.job_list)
        HUGENUM = WAREHOUSE_DIM**10

        RECEIVING = self.receiving  # location of receiving
        SHIPPING = self.shipping  # location of shipping
        LAB = self.lab  # location of lab

        #INITIALIZATIONS
        Which_fork = [1000 for j in range(N_JOBS)] #Which_fork[i] = which forklift job i is assigned to 
        Order_jobs = [] #Order_jobs[i] = the place in line that job i is being done
        Current_job = [0 for j in range(N_FORKLIFTS)] #Current_job[i] = job forklift i is working on
        currentjobsdone = 0 #number of jobs currently assigned
        jobs_done = [0 for j in range(N_JOBS)] #0 if job is not assigned, 1 if job is assigned
        finish_job_time = [0 for j in range(N_FORKLIFTS)] #finish_job_time[i] = estimated time forklift i will finish job Current_job[i]

        JobType = [0 for j in range(N_JOBS)] #record which type of job each is
        num_receiving_jobs = 0.0
        num_shipping_jobs = 0.0
        num_lab_jobs = 0.0
        for i in range(0,N_JOBS):
            if all(job_list[i][0] == RECEIVING):
                JobType[i] = 'R'
                num_receiving_jobs += 1
            elif all(job_list[i][-1] == SHIPPING):
                JobType[i] = 'S'
                num_shipping_jobs += 1
            elif all(job_list[i][-1] == LAB):
                JobType[i] = 'L'
                num_lab_jobs += 1

        #which forklift prefers each of the three regions: in proportion to R/S/L
        num_forklifts_lab = max(int(np.floor((num_receiving_jobs / N_JOBS) * N_FORKLIFTS)),1)
        num_forklifts_shipping = max(int(np.floor((num_shipping_jobs / N_JOBS) * N_FORKLIFTS)),1)
        num_forklifts_receiving = N_FORKLIFTS - num_forklifts_lab - num_forklifts_shipping


        forklift_preference = []
        for i in range(0,num_forklifts_receiving):
            forklift_preference.append('R')
        for i in range(0,num_forklifts_shipping):
            forklift_preference.append('S')
        for i in range(0,num_forklifts_lab):
            forklift_preference.append('L')

        #print('forklift_preference:', forklift_preference)



        #DISTANCEMATRIX
        Mdist = [[0 for j in range(N_JOBS)] for i in range(N_JOBS)]
        # [i][j] entry will be distance from end of job i to beginning of job j
        FirstRow = [0 for j in range(N_JOBS)]

        for i in range(0,N_JOBS):
            for j in range(0,N_JOBS):
                if i != j:
                    Mdist[i][j] = abs(job_list[i][-1][0]-job_list[j][0][0]) + abs(job_list[i][-1][1]-job_list[j][0][1])
            FirstRow[i] = abs(job_list[i][0][0]) + abs(job_list[i][0][1])



        #choose first N_FORKLIFTS jobs, structured so each forklift is forced to do a job of their assigned type
        for i in range(0,N_FORKLIFTS):
            if forklift_preference[i] == 'R': #receiving forklift
                last_job = -1
                next_job_index = FirstRow.index(min(FirstRow))
                Current_job[i] = next_job_index
                FirstRow[next_job_index] = HUGENUM #set it to be huge so it's not chosen again
                jobs_done[next_job_index] = 1
                Order_jobs.append(next_job_index)
                Which_fork[next_job_index] = i

                job = copy.copy(job_list[next_job_index])
                finish_job_time[i] = self.length_job(job) + 15*(len(job)-1)

                currentjobsdone += 1
                #print('forklift', i, 'at time 0 does job ', next_job_index)
            else:
                last_job = -1

                FirstRowi = copy.copy(FirstRow)
                for j in range(0,N_JOBS):
                    if forklift_preference[i] != JobType[j]:
                        FirstRowi[j] = HUGENUM

                next_job_index = FirstRow.index(min(FirstRowi))
                Current_job[i] = next_job_index

                job = copy.copy(job_list[next_job_index])
                finish_job_time[i] = FirstRow[next_job_index] + self.length_job(job) + 15*(len(job)-1)


                FirstRow[next_job_index] = HUGENUM #set it to be huge so it's not chosed again
                jobs_done[next_job_index] = 1
                Order_jobs.append(next_job_index)
                Which_fork[next_job_index] = i

                currentjobsdone += 1
                #print('forklift', i, 'at time 0 does job ', next_job_index)





        while currentjobsdone < N_JOBS: #while loop to assign next job as a forklift finished previous job
            firstforkliftdone = finish_job_time.index(min(finish_job_time))

            last_job = Current_job[firstforkliftdone]
            row = copy.copy(Mdist[last_job])

            for i in range(0,N_JOBS):
                if jobs_done[i] == 1: #if job has been completed
                    row[i] = HUGENUM #i.e. cross out that row
                else: #if job is not completed, weight it!
                    if forklift_preference[firstforkliftdone] == JobType[i]:
                        row[i] = weight*row[i]


            next_job_index = row.index(min(row))
            next_job = copy.copy(job_list[next_job_index])
            #print('forklift', firstforkliftdone, 'finished job', last_job, 'at time ', finish_job_time[firstforkliftdone], 'does job ', next_job_index)
            #ignore picking times and error
            finish_job_time[firstforkliftdone] += \
                Mdist[Current_job[firstforkliftdone]][next_job_index] + self.length_job(next_job) + \
                15*(len(job)-1)

            Current_job[firstforkliftdone] = next_job_index
            jobs_done[next_job_index] = 1
            Order_jobs.append(next_job_index)
            Which_fork[next_job_index] = firstforkliftdone
            currentjobsdone +=1
        
        order = Order_jobs
        which_forklift_does_job_list_reordered = [Which_fork[i] for i in order]
        job_list_reordered = [job_list[i] for i in order]
        
        return [job_list_reordered, which_forklift_does_job_list_reordered]
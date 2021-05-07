import sys
from optparse import OptionParser
import random


SCHED_SWITCH_ON_IO = 'SWITCH_ON_IO'
SCHED_SWITCH_ON_END = 'SWITCH_ON_END'


IO_RUN_LATER = 'IO_RUN_LATER'
IO_RUN_IMMEDIATE = 'IO_RUN_IMMEDIATE'


STATE_RUNNING = 'RUNNING'
STATE_READY = 'READY'
STATE_DONE = 'DONE'
STATE_WAIT = 'WAITING'


PROC_CODE = 'code_'
PROC_PC = 'pc_'
PROC_ID = 'pid_'
PROC_STATE = 'proc_state_'


DO_COMPUTE = 'cpu'
DO_IO = 'io'


class scheduler:

    def __init__(self,process_switch_behavior,
                 io_done_behavior,io_length):
        self.proc_info = {}
        self.process_switch_behavior = process_switch_behavior
        self.io_done_behavior = io_done_behavior
        self.io_length = io_length

    def new_process(self):
        proc_id = len(self.proc_info)
        self.proc_info[proc_id] = {}
        self.proc_info[proc_id][PROC_PC] = 0
        self.proc_info[proc_id][PROC_ID] = proc_id
        self.proc_info[proc_id][PROC_CODE] = []
        self.proc_info[proc_id][PROC_STATE] = STATE_READY
        return proc_id

    def load_file(self,progfile):
        fd = open(progfile)
        proc_id = self.new_process()

        for line in fd:
            tmp = line.split()
            if len(tmp) == 0:
                continue
            opcode = tmp[0]
            if opcode == 'compute':
                assert(len(tmp) == 2)
                for i in range(int(tmp[1])):
                    self.proc_info[proc_id][PROC_CODE].append(DO_COMPUTE)
            elif opcode == 'io':
                assert(len(tmp) == 1)
                self.proc_info[proc_id][PROC_CODE].append(DO_IO)
        fd.close()
        return

    def load(self,program_description):
        proc_id = self.new_process()
        tmp = program_description.split(':')
        if len(tmp) != 2:
            print 'bad description %s : must be number <x:y>' % program_description
            print ' where x is the number of instructions'
            print ' and y is the percent change that an instruction is cpu not io'
            exit(1)

        num_instructions, change_cpu = int(tmp[0]),float(tmp[1])/100.0
        for i in range(num_instructions):
            if random.random() < change_cpu:
                self.proc_info[proc_id][PROC_CODE].append(DO_COMPUTE)
            else:
                self.proc_info[proc_id][PROC_CODE].append(DO_IO)
        return

    def move_to_ready(self,expected,pid=-1):
        if pid == -1:
            pid = self.curr_proc
        assert(self.proc_info[pid][PROC_STATE] == expected)
        self.proc_info[pid][PROC_STATE] = STATE_READY
        return

    def move_to_running(self,expected):
        assert(self.proc_info[self.curr_proc][PROC_STATE] == expected)
        self.proc_info[self.curr_proc][PROC_STATE] = STATE_RUNNING
        return

    def move_to_done(self,expected):
        assert(self.proc_info[self.curr_proc][PROC_STATE] == expected)
        self.proc_info[self.curr_proc][PROC_STATE] = STATE_DONE
        return

    def next_proc(self,pid=-1):
        if pid == -1:
            self.curr_proc = pid
            self.move_to_running(STATE_READY)
            return

        for pid in range(self.curr_proc+1,len(self.proc_info)):
            if self.proc_info[pid][PROC_STATE] == STATE_READY:
                self.curr_proc = pid
                self.move_to_running(STATE_READY)
                return
        for pid in range(0,self.curr_proc+1):
            if self.proc_info[pid][PROC_STATE] == STATE_READY:
                self.curr_proc = pid
                self.move_to_running(STATE_READY)
                return
        return

    def get_num_processes(self):
        return len(self.proc_info)

    def get_num_instruction(self,pid):
        return len(self.proc_info[pid][PROC_CODE])

    def get_instruction(self,pid,index):
        return self.proc_info[pid][PROC_CODE][index]

    def get_num_activate(self):
        num_activate = 0
        for pid in range(len(self.proc_info)):
            if self.proc_info[pid][PROC_STATE] != STATE_DONE:
                num_activate += 1
        return num_activate

    def get_num_runnable(self):
        num_activate = 0
        for pid in range(len(self.proc_info)):
            if self.proc_info[pid][PROC_STATE] == STATE_READY or \
                self.proc_info[pid][PROC_STATE] == STATE_RUNNING:
                num_activate += 1
        return num_activate

    def get_ios_in_flight(self,current_time):
        num_in_flight = 0
        for pid in range(len(self.proc_info)):
            for t in self.io_finish_times[pid]:
                if t > current_time:
                    num_in_flight += 1
        return num_in_flight

    def check_for_switch(self):
        return

    def space(self,num_columns):
        for i in range(num_columns):
            print '%10s' % ' '


    def check_if_done(self):
        if len(self.proc_info[self.curr_proc][PROC_CODE] == 0):
            if self.proc_info[self.curr_proc][PROC_STATE] == STATE_RUNNING:
                self.move_to_done(STATE_RUNNING)
                self.next_proc()
        return

    def run(self):
        clock_tick = 0

        if len(self.proc_info) == 0:
            return

        self.io_finish_times = {}
        for pid in range(len(self.proc_info)):
            self.io_finish_times[pid] = []


        self.curr_proc = 0
        self.move_to_running(STATE_RUNNING)

        print '%s' % 'Time',
        for pid in range(len(self.proc_info)):
            print '%10s' % ('PID:%2d' % (pid))

        print '%10s' % 'CPU',
        print '%10s' % 'IOs',
        print ''


        io_busy = 0
        cpu_busy = 0

        while self.get_num_activate() > 0:

            clock_tick += 1

            io_done = False

            for pid in range(len(self.proc_info)):
                if clock_tick in self.io_finish_times[pid]:
                    io_done = True
                    self.move_to_ready(STATE_WAIT,pid)
                    if self.io_done_behavior == IO_RUN_IMMEDIATE:
                        if self.curr_proc != pid:
                            if self.proc_info[self.curr_proc][PROC_STATE] == STATE_RUNNING:
                                self.move_to_ready(STATE_RUNNING)
                        self.next_proc(pid)
                else:
                    pass



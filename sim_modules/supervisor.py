from settings import *
from modules.func.utils import *
from plot_results import *

import multiprocessing as mp
import os
import socket
import subprocess
import sys
import time

class Supervisor():

    def __init__(self, **mods_dict):
        #Instantiate events
        event_rxtcp = mp.Event() #RX TCP connection event
        event_txtcp = mp.Event() #TX TCP connection event
        event_start = mp.Event() #simulation run start event
        event_end   = mp.Event() #simulation run end event
        #Define events dictionary
        events_dict = {'event_rxtcp':event_rxtcp, 'event_txtcp':event_txtcp, 'event_start':event_start, 'event_end':event_end}
        #Instantiate pipes
        act2csv_out, act2csv_in = mp.Pipe() #actuation data pipe to CSV
        act2tx_out, act2tx_in   = mp.Pipe() #actuation data pipe to TX telemetry
        cm2act_out, cm2act_in   = mp.Pipe() #control model data pipe to actuation
        cm2csv_out, cm2csv_in   = mp.Pipe() #control model data pipe to CSV
        eq2cm_out, eq2cm_in     = mp.Pipe() #equilibrium point data pipe to control model
        eq2csv_out, eq2csv_in   = mp.Pipe() #equilibrium point data pipe to CSV
        dyn2csv_out, dyn2csv_in = mp.Pipe() #dynamics data pipe to CSV
        rx2act_out, rx2act_in   = mp.Pipe() #RX telemetry data pipe to actuation
        rx2cm_out, rx2cm_in     = mp.Pipe() #RX telemetry data pipe to control model
        rx2csv_out, rx2csv_in   = mp.Pipe() #RX telemetry data pipe to CSV
        rx2dyn_out, rx2dyn_in   = mp.Pipe() #RX telemetry data pipe to dynamics 
        rx2eq_out, rx2eq_in     = mp.Pipe() #RX telemetry data pipe to equilibrium
        rx2sp_out, rx2sp_in     = mp.Pipe() #RX telemetry data pipe to setpoint
        rx2sup_out, rx2sup_in   = mp.Pipe() #RX telemetry data pipe to supervisor
        sp2act_out, sp2act_in   = mp.Pipe() #setpoint data pipe to actuation
        sp2cm_out, sp2cm_in     = mp.Pipe() #setpoint data pipe to control model
        sp2csv_out, sp2csv_in   = mp.Pipe() #setpoint data pipe to CSV
        #Define pipes dictionary
        pipes_dict = {'act2csv_out':act2csv_out, 'act2csv_in':act2csv_in, 'act2tx_out':act2tx_out, 'act2tx_in':act2tx_in, 'cm2act_out':cm2act_out, 'cm2act_in':cm2act_in, 'cm2csv_out':cm2csv_out, 'cm2csv_in':cm2csv_in, 'eq2cm_out':eq2cm_out, 'eq2cm_in':eq2cm_in, 'eq2csv_out':eq2csv_out, 'eq2csv_in':eq2csv_in, 'dyn2csv_out':dyn2csv_out, 'dyn2csv_in':dyn2csv_in, 'rx2act_out':rx2act_out, 'rx2act_in':rx2act_in, 'rx2cm_out':rx2cm_out, 'rx2cm_in':rx2cm_in, 'rx2csv_out':rx2csv_out, 'rx2csv_in':rx2csv_in, 'rx2dyn_out':rx2dyn_out, 'rx2dyn_in':rx2dyn_in, 'rx2eq_out':rx2eq_out, 'rx2eq_in':rx2eq_in, 'rx2sp_out':rx2sp_out, 'rx2sp_in':rx2sp_in, 'rx2sup_out':rx2sup_out, 'rx2sup_in':rx2sup_in, 'sp2act_out':sp2act_out, 'sp2act_in':sp2act_in, 'sp2cm_out':sp2cm_out, 'sp2cm_in':sp2cm_in, 'sp2csv_out':sp2csv_out, 'sp2csv_in':sp2csv_in}
        #Define global dictionary
        self.global_dict = {**events_dict, **pipes_dict, **mods_dict}
        #Select type of simulation
        if (SIM_TYPE == 0) or (SIM_TYPE == 'single'):
            self.single_sim()
        elif (SIM_TYPE == 1) or (SIM_TYPE == 'multiple'):
            self.multiple_sim()

    def start_processes(self):
        #Instantiate processes
        act_proc = self.actuation_process()
        cm_proc  = self.control_model_process()
        cfg_proc = self.configuration_process()
        dyn_proc = self.dynamics_process()
        eq_proc  = self.equilibrium_process()
        sp_proc  = self.setpoint_process()
        telemrx_proc, telemtx_proc = self.telemetry_processes()
        cmlog_proc, dynlog_proc, eqlog_proc, splog_proc, telemrxlog_proc, telemtxlog_proc = self.csvlogging_processes()
        #Start processes (order is important)
        telemrx_proc.start()
        telemtx_proc.start()
        cfg_proc.start()
        act_proc.start()
        cm_proc.start()
        dyn_proc.start()
        eq_proc.start()
        sp_proc.start()
        cmlog_proc.start()
        dynlog_proc.start()
        eqlog_proc.start()
        splog_proc.start()
        telemrxlog_proc.start()
        telemtxlog_proc.start()
        time.sleep(1)
        scen_proc = self.scenario_process() #scenario subprocess automatically starts when called
        #Update global dictionary with new processes
        self.global_dict.update(act_proc = act_proc)
        self.global_dict.update(cfg_proc = cfg_proc)
        self.global_dict.update(cm_proc = cm_proc)
        self.global_dict.update(cmlog_proc = cmlog_proc)
        self.global_dict.update(dyn_proc = dyn_proc)
        self.global_dict.update(dynlog_proc = dynlog_proc)
        self.global_dict.update(eq_proc = eq_proc)
        self.global_dict.update(eqlog_proc = eqlog_proc)
        self.global_dict.update(scen_proc = scen_proc)
        self.global_dict.update(sp_proc = sp_proc)
        self.global_dict.update(splog_proc = splog_proc)
        self.global_dict.update(telemrx_proc = telemrx_proc)
        self.global_dict.update(telemrxlog_proc = telemrxlog_proc)
        self.global_dict.update(telemtx_proc = telemtx_proc)
        self.global_dict.update(telemtxlog_proc = telemtxlog_proc)

    def terminate_processes(self):
        #Get processes
        act_proc        = self.global_dict['act_proc']
        cfg_proc        = self.global_dict['cfg_proc']
        cm_proc         = self.global_dict['cm_proc']
        cmlog_proc      = self.global_dict['cmlog_proc']
        dyn_proc        = self.global_dict['dyn_proc']
        dynlog_proc     = self.global_dict['dynlog_proc']
        eq_proc         = self.global_dict['eq_proc']
        eqlog_proc      = self.global_dict['eqlog_proc']
        scen_proc       = self.global_dict['scen_proc']
        sp_proc         = self.global_dict['sp_proc']
        splog_proc      = self.global_dict['splog_proc']
        telemrx_proc    = self.global_dict['telemrx_proc']
        telemrxlog_proc = self.global_dict['telemrxlog_proc']
        telemtx_proc    = self.global_dict['telemtx_proc']
        telemtxlog_proc = self.global_dict['telemtxlog_proc']
        #Terminate processes (order is important)
        scen_proc.terminate()
        time.sleep(1)
        act_proc.terminate()
        cm_proc.terminate()
        dyn_proc.terminate()
        eq_proc.terminate()
        sp_proc.terminate()
        cfg_proc.terminate()
        telemtx_proc.terminate()
        telemrx_proc.terminate()
        cmlog_proc.terminate()
        dynlog_proc.terminate()
        eqlog_proc.terminate()
        splog_proc.terminate()
        telemrxlog_proc.terminate()
        telemtxlog_proc.terminate()
        #Update global dictionary with new processes
        self.global_dict.update(act_proc = act_proc)
        self.global_dict.update(cfg_proc = cfg_proc)
        self.global_dict.update(cm_proc = cm_proc)
        self.global_dict.update(cmlog_proc = cmlog_proc)
        self.global_dict.update(dyn_proc = dyn_proc)
        self.global_dict.update(eq_proc = eq_proc)
        self.global_dict.update(dynlog_proc = dynlog_proc)
        self.global_dict.update(eqlog_proc = eqlog_proc)
        self.global_dict.update(scen_proc = scen_proc)
        self.global_dict.update(sp_proc = sp_proc)
        self.global_dict.update(splog_proc = splog_proc)
        self.global_dict.update(telemrx_proc = telemrx_proc)
        self.global_dict.update(telemrxlog_proc = telemrxlog_proc)
        self.global_dict.update(telemtx_proc = telemtx_proc)
        self.global_dict.update(telemtxlog_proc = telemtxlog_proc)

    def clear_events(self):
        #Get events
        event_rxtcp = self.global_dict['event_rxtcp']
        event_txtcp = self.global_dict['event_txtcp']
        event_start = self.global_dict['event_start']
        event_end   = self.global_dict['event_end']
        #Clear events
        event_rxtcp.clear()
        event_txtcp.clear()
        event_start.clear()
        event_end.clear()
        #Update global dictionary with cleared events
        self.global_dict.update(event_rxtcp = event_rxtcp)
        self.global_dict.update(event_txtcp = event_txtcp)
        self.global_dict.update(event_start = event_start)
        self.global_dict.update(event_end = event_end)

    def restore_pipes(self):
        #Get pipes
        act2csv_out = self.global_dict['act2csv_out']
        act2csv_in  = self.global_dict['act2csv_in']
        act2tx_out  = self.global_dict['act2tx_out']
        act2tx_in   = self.global_dict['act2tx_in']
        cm2act_out  = self.global_dict['cm2act_out']
        cm2act_in   = self.global_dict['cm2act_in']
        cm2csv_out  = self.global_dict['cm2csv_out']
        cm2csv_in   = self.global_dict['cm2csv_in']
        dyn2csv_out = self.global_dict['dyn2csv_out']
        dyn2csv_in  = self.global_dict['dyn2csv_in']
        eq2cm_out   = self.global_dict['eq2cm_out']
        eq2cm_in    = self.global_dict['eq2cm_in']
        eq2csv_out  = self.global_dict['eq2csv_out']
        eq2csv_in   = self.global_dict['eq2csv_in']
        rx2act_out  = self.global_dict['rx2act_out']
        rx2act_in   = self.global_dict['rx2act_in']
        rx2cm_out   = self.global_dict['rx2cm_out']
        rx2cm_in    = self.global_dict['rx2cm_in']
        rx2csv_out  = self.global_dict['rx2csv_out']
        rx2csv_in   = self.global_dict['rx2csv_in']
        rx2dyn_out  = self.global_dict['rx2dyn_out']
        rx2dyn_in   = self.global_dict['rx2dyn_in']
        rx2eq_out   = self.global_dict['rx2eq_out']
        rx2eq_in    = self.global_dict['rx2eq_in']
        rx2sp_out   = self.global_dict['rx2sp_out']
        rx2sp_in    = self.global_dict['rx2sp_in']
        rx2sup_out  = self.global_dict['rx2sup_out']
        rx2sup_in   = self.global_dict['rx2sup_in']
        sp2act_out  = self.global_dict['sp2act_out']
        sp2act_in   = self.global_dict['sp2act_in']
        sp2cm_out   = self.global_dict['sp2cm_out']
        sp2cm_in    = self.global_dict['sp2cm_in']
        sp2csv_out  = self.global_dict['sp2csv_out']
        sp2csv_in   = self.global_dict['sp2csv_in']
        #Create new pipes
        act2csv_out, act2csv_in = mp.Pipe() #actuation data pipe to CSV
        act2tx_out, act2tx_in   = mp.Pipe() #actuation data pipe to TX telemetry
        cm2act_out, cm2act_in   = mp.Pipe() #control model data pipe to actuation
        cm2csv_out, cm2csv_in   = mp.Pipe() #control model data pipe to CSV
        dyn2csv_out, dyn2csv_in = mp.Pipe() #dynamics data pipe to CSV
        eq2cm_out, eq2cm_in     = mp.Pipe() #equilibrium point data pipe to control model
        eq2csv_out, eq2csv_in   = mp.Pipe() #equilibrium point data pipe to CSV
        rx2act_out, rx2act_in   = mp.Pipe() #RX telemetry data pipe to actuation
        rx2cm_out, rx2cm_in     = mp.Pipe() #RX telemetry data pipe to control model
        rx2csv_out, rx2csv_in   = mp.Pipe() #RX telemetry data pipe to CSV
        rx2dyn_out, rx2dyn_in   = mp.Pipe() #RX telemetry data pipe to dynamics 
        rx2eq_out, rx2eq_in     = mp.Pipe() #RX telemetry data pipe to equilibrium point
        rx2sp_out, rx2sp_in     = mp.Pipe() #RX telemetry data pipe to setpoint
        rx2sup_out, rx2sup_in   = mp.Pipe() #RX telemetry data pipe to supervisor
        sp2act_out, sp2act_in   = mp.Pipe() #setpoint data pipe to actuation
        sp2cm_out, sp2cm_in     = mp.Pipe() #setpoint data pipe to control model
        sp2csv_out, sp2csv_in   = mp.Pipe() #setpoint data pipe to CSV
        #Update global dictionary with new pipes
        self.global_dict.update(act2csv_out = act2csv_out)
        self.global_dict.update(act2csv_in = act2csv_in)
        self.global_dict.update(act2tx_out = act2tx_out)
        self.global_dict.update(act2tx_in = act2tx_in)
        self.global_dict.update(cm2act_out = cm2act_out)
        self.global_dict.update(cm2act_in = cm2act_in)
        self.global_dict.update(cm2csv_out = cm2csv_out)
        self.global_dict.update(cm2csv_in = cm2csv_in)
        self.global_dict.update(dyn2csv_out = dyn2csv_out)
        self.global_dict.update(dyn2csv_in = dyn2csv_in)
        self.global_dict.update(eq2cm_out = eq2cm_out)
        self.global_dict.update(eq2cm_in = eq2cm_in)
        self.global_dict.update(eq2csv_out = eq2csv_out)
        self.global_dict.update(eq2csv_in = eq2csv_in)
        self.global_dict.update(rx2act_out = rx2act_out)
        self.global_dict.update(rx2act_in = rx2act_in)
        self.global_dict.update(rx2cm_out = rx2cm_out)
        self.global_dict.update(rx2cm_in = rx2cm_in)
        self.global_dict.update(rx2csv_out = rx2csv_out)
        self.global_dict.update(rx2csv_in = rx2csv_in)
        self.global_dict.update(rx2dyn_out = rx2dyn_out)
        self.global_dict.update(rx2dyn_in = rx2dyn_in)
        self.global_dict.update(rx2eq_out = rx2eq_out)
        self.global_dict.update(rx2eq_in = rx2eq_in)
        self.global_dict.update(rx2sp_out = rx2sp_out)
        self.global_dict.update(rx2sp_in = rx2sp_in)
        self.global_dict.update(rx2sup_out = rx2sup_out)
        self.global_dict.update(rx2sup_in = rx2sup_in)
        self.global_dict.update(sp2act_out = sp2act_out)
        self.global_dict.update(sp2act_in = sp2act_in)
        self.global_dict.update(sp2cm_out = sp2cm_out)
        self.global_dict.update(sp2cm_in = sp2cm_in)
        self.global_dict.update(sp2csv_out = sp2csv_out)
        self.global_dict.update(sp2csv_in = sp2csv_in)

    def actuation_process(self):
        #Get process arguments
        act_mod     = self.global_dict['act_mod']
        act2csv_in  = self.global_dict['act2csv_in']
        act2tx_in   = self.global_dict['act2tx_in']
        cm2act_out  = self.global_dict['cm2act_out']
        rx2act_out  = self.global_dict['rx2act_out']
        event_start = self.global_dict['event_start']
        event_end   = self.global_dict['event_end']
        #Instantiate actuation process
        if (ACT_TYPE == 0) or (ACT_TYPE == 'random'): #random control
            act_proc = mp.Process(target=act_mod.Random.run, args=(act2csv_in, act2tx_in, rx2act_out, event_start, event_end), daemon=True)
        elif (ACT_TYPE == 1) or (ACT_TYPE == 'fsfb'): #full-state feedback control
            act_proc = mp.Process(target=act_mod.FSFB.run, args=(act2csv_in, act2tx_in, cm2act_out, rx2act_out, event_start, event_end), daemon=True)
        elif (ACT_TYPE == 2) or (ACT_TYPE == 'lqr'): #linear-quadratic regulator
            act_proc = mp.Process(target=act_mod.LQR.run, args=(act2csv_in, act2tx_in, cm2act_out, rx2act_out, event_start, event_end), daemon=True)
        elif (ACT_TYPE == 3) or (ACT_TYPE == 'mpc'): #model predictive control
            act_proc = mp.Process(target=act_mod.MPC.run, args=(act2csv_in, act2tx_in, cm2act_out, rx2act_out, event_start, event_end), daemon=True)
        return act_proc

    def control_model_process(self):
        #Get process arguments
        cm_mod      = self.global_dict['cm_mod']
        cm2act_in   = self.global_dict['cm2act_in']
        cm2csv_in   = self.global_dict['cm2csv_in']
        eq2cm_out   = self.global_dict['eq2cm_out']
        eq2csv_in   = self.global_dict['eq2csv_in']
        rx2cm_out   = self.global_dict['rx2cm_out']
        sp2cm_out   = self.global_dict['sp2cm_out']
        event_start = self.global_dict['event_start']
        event_end   = self.global_dict['event_end']
        #Instantiate control model process
        if (CM_TYPE == 0) or (CM_TYPE == 'AL'): #analytic linear control model
            cm_proc = mp.Process(target=cm_mod.ALCM.run, args=(cm2act_in, cm2csv_in, eq2cm_out, rx2cm_out, sp2cm_out, event_start, event_end), daemon=True)
        elif (CM_TYPE == 1) or (CM_TYPE == 'ANL'): #analytic non-linear control model
            cm_proc = mp.Process(target=cm_mod.ANLCM.run, args=(cm2act_in, cm2csv_in, eq2cm_out, rx2cm_out, sp2cm_out, event_start, event_end), daemon=True)
        elif (CM_TYPE == 2) or (CM_TYPE == 'LANL'): #linearized analytic non-linear control model
            cm_proc = mp.Process(target=cm_mod.LANLCM.run, args=(cm2act_in, cm2csv_in, eq2cm_out, rx2cm_out, sp2cm_out, event_start, event_end), daemon=True)
        return cm_proc

    def configuration_process(self):
        #Get process arguments
        cfg_mod     = self.global_dict['cfg_mod']
        event_rxtcp = self.global_dict['event_rxtcp']
        #Instantiate configuration process
        cfg_proc    = mp.Process(target=cfg_mod.transmit, args=(event_rxtcp,), daemon=True)
        return cfg_proc

    def equilibrium_process(self):
        #Get process arguments
        eq_mod      = self.global_dict['eq_mod']
        eq2cm_in    = self.global_dict['eq2cm_in']
        eq2csv_in   = self.global_dict['eq2csv_in']
        rx2eq_out   = self.global_dict['rx2eq_out']
        event_start = self.global_dict['event_start']
        event_end   = self.global_dict['event_end']
        #Instantiate equilibrium process
        eq_proc = mp.Process(target=eq_mod.run, args=(eq2cm_in, eq2csv_in, rx2eq_out, event_start, event_end), daemon=True)
        return eq_proc

    def setpoint_process(self):
        #Get process arguments
        sp_mod      = self.global_dict['sp_mod']
        rx2sp_out   = self.global_dict['rx2sp_out']
        sp2cm_in    = self.global_dict['sp2cm_in']
        sp2csv_in   = self.global_dict['sp2csv_in']
        event_start = self.global_dict['event_start']
        event_end   = self.global_dict['event_end']
        #Instantiate setpoint process
        if (SP_TYPE == 0) or (SP_TYPE == 'constant'): #constant setpoint
            sp_proc = mp.Process(target=sp_mod.Constant.run, args=(rx2sp_out, sp2cm_in, sp2csv_in, event_start, event_end), daemon=True)
        elif (SP_TYPE == 1) or (SP_TYPE == 'straight_line'): #straight line setpoint
            sp_proc = mp.Process(target=sp_mod.StraightLine.run, args=(rx2sp_out, sp2cm_in, sp2csv_in, event_start, event_end), daemon=True)
        return sp_proc

    def dynamics_process(self):
        #Get process arguments
        dyn_mod     = self.global_dict['dyn_mod']
        dyn2csv_in  = self.global_dict['dyn2csv_in']
        rx2dyn_out  = self.global_dict['rx2dyn_out']
        event_start = self.global_dict['event_start']
        event_end   = self.global_dict['event_end']
        #Instantiate dynamics process
        dyn_proc    = mp.Process(target=dyn_mod.run, args=(dyn2csv_in, rx2dyn_out, event_start, event_end), daemon=True)
        return dyn_proc

    def csvlogging_processes(self):
        #Get process arguments
        csvlog_mod      = self.global_dict['csvlog_mod']
        csvlog_dir      = self.global_dict['csvlog_dir']
        act2csv_out     = self.global_dict['act2csv_out']
        cm2csv_out      = self.global_dict['cm2csv_out']
        dyn2csv_out     = self.global_dict['dyn2csv_out']
        eq2csv_out      = self.global_dict['eq2csv_out']
        rx2csv_out      = self.global_dict['rx2csv_out']
        sp2csv_out      = self.global_dict['sp2csv_out']
        event_start     = self.global_dict['event_start']
        event_end       = self.global_dict['event_end']
        #Instantiate CSV logging processes
        cmlog_proc      = mp.Process(target=csvlog_mod.write_cmlog, args=(csvlog_dir, cm2csv_out, event_start, event_end), daemon=True) #logging control model
        dynlog_proc     = mp.Process(target=csvlog_mod.write_dynlog, args=(csvlog_dir, dyn2csv_out, event_start, event_end), daemon=True) #logging dynamics
        eqlog_proc      = mp.Process(target=csvlog_mod.write_eqlog, args=(csvlog_dir, eq2csv_out, event_start, event_end), daemon=True) #logging equilibrium point
        splog_proc      = mp.Process(target=csvlog_mod.write_splog, args=(csvlog_dir, sp2csv_out, event_start, event_end), daemon=True) #logging setpoint
        telemrxlog_proc = mp.Process(target=csvlog_mod.write_telemrxlog, args=(csvlog_dir, rx2csv_out, event_start, event_end), daemon=True) #logging RX telemetry
        telemtxlog_proc = mp.Process(target=csvlog_mod.write_telemtxlog, args=(csvlog_dir, act2csv_out, event_start, event_end), daemon=True) #logging TX telemetry
        return cmlog_proc, dynlog_proc, eqlog_proc, splog_proc, telemrxlog_proc, telemtxlog_proc

    def plot_sim_results(self):
        #Get arguments
        csvlog_mod = self.global_dict['csvlog_mod']
        csvlog_dir = self.global_dict['csvlog_dir']
        csvlog_mod.read_cmlog(csvlog_dir)
        rxdata  = csvlog_mod.read_telemrxlog(csvlog_dir)
        txdata  = csvlog_mod.read_telemtxlog(csvlog_dir)
        dyndata = csvlog_mod.read_dynlog(csvlog_dir)
        eqdata  = csvlog_mod.read_eqlog(csvlog_dir)
        spdata  = csvlog_mod.read_splog(csvlog_dir)
        plot(rxdata, txdata, dyndata, eqdata, spdata)

    def scenario_process(self):
        #Get process arguments
        scen_mod = self.global_dict['scen_mod']
        #Instantiate scenario process
        shell_command = scen_mod.run()
        scen_proc     = subprocess.Popen(args=shell_command)
        return scen_proc

    def telemetry_processes(self):
        #Get process arguments
        telem_mod   = self.global_dict['telem_mod']
        act2tx_out  = self.global_dict['act2tx_out']
        rx2act_in   = self.global_dict['rx2act_in']
        rx2cm_in    = self.global_dict['rx2cm_in']
        rx2csv_in   = self.global_dict['rx2csv_in']
        rx2dyn_in   = self.global_dict['rx2dyn_in']
        rx2eq_in    = self.global_dict['rx2eq_in']
        rx2sp_in    = self.global_dict['rx2sp_in']
        rx2sup_in   = self.global_dict['rx2sup_in']
        event_rxtcp = self.global_dict['event_rxtcp']
        event_txtcp = self.global_dict['event_txtcp']
        event_start = self.global_dict['event_start']
        event_end   = self.global_dict['event_end']
        #Instantiate telemetry processes
        telemrx_proc = mp.Process(target=telem_mod.receive, args=(rx2act_in, rx2cm_in, rx2csv_in, rx2dyn_in, rx2eq_in, rx2sp_in, rx2sup_in, event_rxtcp, event_start, event_end), daemon=True) #RX telemetry
        telemtx_proc = mp.Process(target=telem_mod.transmit, args=(act2tx_out, event_rxtcp, event_txtcp, event_start, event_end), daemon=True) #TX telemetry
        return telemrx_proc, telemtx_proc

    def single_sim(self):
        self.make_log_dir() #create CSV log directory
        self.csvlog_headers() #write CSV log headers
        self.start_processes() #start simulation processes
        rx2sup_out  = self.global_dict['rx2sup_out']
        event_start = self.global_dict['event_start']
        event_end   = self.global_dict['event_end']
        event_start.wait() #wait for simulation start event
        #Single simulation run loop
        while True:
            try:
                rxdata    = rx2sup_out.recv() #receive RX telemetry
                lastframe = rxdata[-1] #get last RX telemetry frame
                terminate_run = self.simulation_watchdog(lastframe) #check if simulation run is over
                if terminate_run:
                    self.terminate_processes() #terminate simulation processes
                    terminate_run = False
                    break
            except:
                raise RuntimeError('.'.join((__name__, sys._getframe().f_code.co_name)))
        self.plot_sim_results()
        quit() #quit program

    def multiple_sim(self):
        self.make_log_dir() #create CSV log directory
        self.csvlog_headers() #write CSV log headers
        #Multiple simulations runs loop
        for _ in range(SIM_ITER_NUM):
            self.start_processes() #start simulation processes
            rx2sup_out  = self.global_dict['rx2sup_out']
            event_start = self.global_dict['event_start']
            event_end   = self.global_dict['event_end']
            event_start.wait() #wait for simulation start event
            #Single simulation run loop
            while True:
                try:
                    rxdata    = rx2sup_out.recv() #receive RX telemetry
                    lastframe = rxdata[-1] #get last RX telemetry frame
                    terminate_run = self.simulation_watchdog(lastframe) #check if simulation run is over
                    if terminate_run:
                        event_end.set() #set simulation end event
                        self.global_dict.update(event_end = event_end)
                        time.sleep(1)
                        self.terminate_processes() #terminate simulation processes
                        self.clear_events() #clear events flags
                        self.restore_pipes() #restore broken pipes
                        terminate_run = False
                        break
                except:
                    raise RuntimeError('.'.join((__name__, sys._getframe().f_code.co_name)))
        quit() #quit program

    def simulation_watchdog(self, lastframe):
        #Watchdog that activates when the aircraft is upside down or its wheels touch down
        up_down = lastframe[110]
        wow1    = lastframe[111]
        wow2    = lastframe[112]
        wow3    = lastframe[113]
        wc1     = lastframe[114]
        wc2     = lastframe[115]
        wc3     = lastframe[116]
        return True if (up_down == 1) or (wow1 == 1) or (wow2 == 1) or (wow3 == 1) or (wc1 == 1) or (wc2 == 1) or (wc3 == 1) else False

    def make_log_dir(self):
        #Make directories for saving logs

        #List directories in csv log path or create csv log dir
        try:
            dir_list = os.listdir(CSV_LOG_DIR)
        except:
            dir_list = []
            os.makedirs(CSV_LOG_DIR, exist_ok=True)
        #List log directories named as integer
        int_log_dir_list = []
        for possible_log_dir in dir_list:
            try:
                int_log_dir_list.append(int(possible_log_dir))
            except:
                continue
        int_log_dir_list = sorted(int_log_dir_list)
        #Create new log directory
        if len(int_log_dir_list) == 0:
            csvlog_dir = os.path.join(CSV_LOG_DIR, '1')
        else:
            last_int   = int_log_dir_list[-1]
            csvlog_dir = os.path.join(CSV_LOG_DIR, str(last_int + 1))
        os.makedirs(csvlog_dir)

        self.global_dict.update(csvlog_dir = csvlog_dir)

    def csvlog_headers(self):
        csvlog_mod = self.global_dict['csvlog_mod']
        csvlog_dir = self.global_dict['csvlog_dir']
        csvlog_mod.header_cmlog(csvlog_dir)
        csvlog_mod.header_dynlog(csvlog_dir)
        csvlog_mod.header_eqlog(csvlog_dir)
        csvlog_mod.header_splog(csvlog_dir)
        csvlog_mod.header_telemrxlog(csvlog_dir)
        csvlog_mod.header_telemtxlog(csvlog_dir)

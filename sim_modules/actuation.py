import numpy as np
import random

from constants import *
from settings import *

class Actuation():

    def __init__(self):
        self.t         = TELEM_WAIT
        self.dt        = 1 / ACT_HZ
        self.simact    = np.zeros(TELEM_TX_LEN) #array for storing actuation
        self.simactstr = np.zeros(TELEM_TX_LEN) #array for storing actuation as string
        self.csvact    = np.zeros(TELEM_TX_LEN + 1) #array for storing csv actuation
        self.actstr    = str()

    def random_control(self, act2csv_in, act2tx_in, rx2act_out, event_start, event_end):
        event_start.wait() #wait for simulation start event
        while True:
            if event_end.is_set():
                #Close pipes
                act2csv_in.close()
                act2tx_in.close()
                rx2act_out.close()
                break
            else:
                rxdata = rx2act_out.recv() #receive RX telemetry
                if (np.any(rxdata[:,0] >= self.t)):
                    i = np.where(rxdata[:,0] >= self.t)[0][0] #find first frame index
                    rxdata = rxdata[i,:] #get first frame
                    self.t = self.t + self.dt
                    for i in range(ACT_LEN):
                        if i == 4 or i == 5:
                            self.simact[i] = random.gauss(mu=0.9, sigma=0.1) #throttle and mixture
                        else:
                            self.simact[i] = random.gauss(mu=0, sigma=0.1)
                    self.csvact[0]  = rxdata[0] #add timestamp
                    self.csvact[1:] = self.simact
                    self.simactstr = self.simact.astype(str)
                    self.actstr = '\t'.join(self.simactstr)
                    self.actstr += '\n'
                    act2tx_in.send(self.actstr) #send actuation to TX telemetry
                    act2csv_in.send(self.csvact) #send actuation to CSV
                else:
                    pass
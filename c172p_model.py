import numpy as np
import math

from scipy import interpolate

from utils import *

''' PARAMETERS '''
BW_FT                 = 35.8000 #wing span
CBARW_FT              = 4.9000 #wing chord
PROP_DIAM_IN          = 75.0000 #propeller diameter
SH_SQFT               = 21.9000 #horizontal tail area
SV_SQFT               = 16.5000 #vertical tail area
SW_SQFT               = 174.0000 #wing area
SPIRAL_PROPWASH_COEFF = 0.2500 #coefficient due to the propeller induced velocity

#Drag coefficient due to ground effect
#Column 0: h_b_mac_ft
kCDge = np.array(   
                    [
                    [0.0000, 0.4800],
                    [0.1000, 0.5150],
                    [0.1500, 0.6290],
                    [0.2000, 0.7090],
                    [0.3000, 0.8150],
                    [0.4000, 0.8820],
                    [0.5000, 0.9280],
                    [0.6000, 0.9620],
                    [0.7000, 0.9880],
                    [0.8000, 1.0000],
                    [0.9000, 1.0000],
                    [1.0000, 1.0000],
                    [1.1000, 1.0000]
                    ]
                )
kCDge_interp = interpolate.interp1d(kCDge[:,0], kCDge[:,1], bounds_error=False, fill_value=(kCDge[0,1], kCDge[-1,1]))

#Drag coefficient due to flaps position
#Column 0: flaps_pos_deg
CD2 = np.array(
                [
                [0.0000, 0.0000],
                [10.0000, 0.0070],
                [20.0000, 0.0120],
                [30.0000, 0.0180]
                ]
              )
CD2_interp = interpolate.interp1d(CD2[:,0], CD2[:,1], bounds_error=False, fill_value=(CD2[0,1], CD2[-1,1]))

#Drag coefficient due to angle of attack and flaps position
#Column 0: alpha_rad | Row 0: flaps_pos_deg
CD3 = np.array(   
                [
                [np.NaN, 0.0000, 10.0000, 20.0000, 30.0000],
                [-0.0873, 0.0041, 0.0000, 0.0005, 0.0014],
                [-0.0698, 0.0013, 0.0004, 0.0025, 0.0041],
                [-0.0524, 0.0001, 0.0023, 0.0059, 0.0084],
                [-0.0349, 0.0003, 0.0057, 0.0108, 0.0141],
                [-0.0175, 0.0020, 0.0105, 0.0172, 0.0212],
                [0.0000 , 0.0052, 0.0168, 0.0251, 0.0299],
                [0.0175 , 0.0099, 0.0248, 0.0346, 0.0402],
                [0.0349 , 0.0162, 0.0342, 0.0457, 0.0521],
                [0.0524 , 0.0240, 0.0452, 0.0583, 0.0655],
                [0.0698 , 0.0334, 0.0577, 0.0724, 0.0804],
                [0.0873 , 0.0442, 0.0718, 0.0881, 0.0968],
                [0.1047 , 0.0566, 0.0874, 0.1053, 0.1148],
                [0.1222 , 0.0706, 0.1045, 0.124 , 0.1343],
                [0.1396 , 0.0860, 0.1232, 0.1442, 0.1554],
                [0.1571 , 0.0962, 0.1353, 0.1573, 0.1690],
                [0.1745 , 0.1069, 0.1479, 0.1708, 0.1830],
                [0.1920 , 0.1180, 0.1610, 0.1849, 0.1975],
                [0.2094 , 0.1298, 0.1746, 0.1995, 0.2126],
                [0.2269 , 0.1424, 0.1892, 0.2151, 0.2286],
                [0.2443 , 0.1565, 0.2054, 0.2323, 0.2464],
                [0.3491 , 0.2537, 0.3298, 0.3755, 0.3983],
                [0.5236 , 0.4500, 0.5850, 0.6660, 0.7065],
                [0.6981 , 0.7000, 0.9100, 1.0360, 1.0990],
                [0.8727 , 1.0000, 1.3000, 1.4800, 1.5700],
                [1.0472 , 1.3500, 1.7550, 1.9980, 2.1195],
                [1.2217 , 1.5000, 1.9500, 2.2200, 2.3550],
                [1.3963 , 1.5700, 2.0410, 2.3236, 2.4649],
                [1.5710 , 1.6000, 2.0800, 2.3680, 2.5120]
                ]
              )
CD3_trans = CD3.transpose()
CD3_interp = interpolate.interp2d(CD3_trans[0,1:], CD3_trans[1:,0], CD3_trans[1:,1:])

#Side force coefficient due to side-slip angle and flaps position
#Column 0: beta_rad | Row 0: flaps_pos_deg
CY1 = np.array(
                [
                [np.NaN, 0.0000, 30.0000],
                [-0.3490, 0.1370, 0.1060],
                [0.0000, 0.0000, 0.0000],
                [0.3490, -0.1370, -0.1060]
                ]
              )
CY1_trans = CY1.transpose()
CY1_interp = interpolate.interp2d(CY1_trans[0,1:], CY1_trans[1:,0], CY1_trans[1:,1:])

#Lift coefficient due to ground effect
#Column 0: h_b_mac_ft
kCLge = np.array(   
                    [
                    [0.0000, 1.2030],
                    [0.1000, 1.1270],
                    [0.1500, 1.0900],
                    [0.2000, 1.0730],
                    [0.3000, 1.0460],
                    [0.4000, 1.0280],
                    [0.5000, 1.0190],
                    [0.6000, 1.0130],
                    [0.7000, 1.0080],
                    [0.8000, 1.0060],
                    [0.9000, 1.0030],
                    [1.0000, 1.0020],
                    [1.1000, 1.0000]
                    ]
                )
kCLge_interp = interpolate.interp1d(kCLge[:,0], kCLge[:,1], bounds_error=False, fill_value=(kCLge[0,1], kCLge[-1,1]))

#Lift coefficient due to alpha and aerodynamic hysteresis
#Column 0: alpha_rad | Row 0: stall_hyst_norm
CL1 = np.array(   
                [
                [np.NaN, 0.0000, 1.0000],
                [-0.0900, -0.2200, -0.2200],
                [0.0000, 0.2500, 0.2500],
                [0.0900, 0.7300, 0.7300],
                [0.1000, 0.8300, 0.7800],
                [0.1200, 0.9200, 0.7900],
                [0.1400, 1.0200, 0.8100],
                [0.1600, 1.0800, 0.8200],
                [0.1700, 1.1300, 0.8300],
                [0.1900, 1.1900, 0.8500],
                [0.2100, 1.2500, 0.8600],
                [0.2400, 1.3500, 0.8800],
                [0.2600, 1.4400, 0.9000],
                [0.2800, 1.4700, 0.9200],
                [0.3000, 1.4300, 0.9500],
                [0.3200, 1.3800, 0.9900],
                [0.3400, 1.3000, 1.0500],
                [0.3600, 1.1500, 1.1500],
                [0.5200, 1.4700, 1.4700],
                [0.7000, 1.6500, 1.6500],
                [0.8700, 1.4700, 1.4700],
                [1.0500, 1.1700, 1.1700],
                [1.5700, 0.0100, 0.0100]
                ]
              )
CL1_trans = CL1.transpose()
CL1_interp = interpolate.interp2d(CL1_trans[0,1:], CL1_trans[1:,0], CL1_trans[1:,1:])

#Lift coefficient due to flaps position
#Column 0: flaps_pos_deg
CL2 = np.array(
                [
                [0.0000, 0.0000],
                [10.0000, 0.2000],
                [20.0000, 0.3000],
                [30.0000, 0.3500]
                ]
              )
CL2_interp = interpolate.interp1d(CL2[:,0], CL2[:,1], bounds_error=False, fill_value=(CL2[0,1], CL2[-1,1]))

#Roll moment coefficient due to alpha wing
#Column 0: alpha_rad
Cl1 = np.array(
                [
                [0.2790, 1.0000],
                [0.2970, 3.5000]
                ]
              )
Cl1_interp = interpolate.interp1d(Cl1[:,0], Cl1[:,1], bounds_error=False, fill_value=(Cl1[0,1], Cl1[-1,1]))

#Roll moment coefficient due to flaps position
#Column 0: flaps_pos_deg
Cl31 = np.array(
                [
                [0.0000, 0.0798],
                [30.000, 0.1246]
                ]
              )
Cl31_interp = interpolate.interp1d(Cl31[:,0], Cl31[:,1], bounds_error=False, fill_value=(Cl31[0,1], Cl31[-1,1]))

#Roll moment coefficient due to flaps position (stall)
#Column 0: alpha_rad | Row 0: r_rad_sec
Cl32 = np.array(
                [
                [np.NaN, -0.1500, -0.1000, 0.0000, 0.1000, 0.1500],
                [0.2970, 35.0000, 30.0000, 1.0000, 30.0000, 35.0000],
                [0.5000, 5.0000, 5.0000, 1.0000, 5.0000, 5.0000]
                ]
              )
Cl32_trans = Cl32.transpose()
Cl32_interp = interpolate.interp2d(Cl32_trans[0,1:], Cl32_trans[1:,0], Cl32_trans[1:,1:])

#Roll moment coefficient due to flaps position
#Column 0: alpha_rad | Row 0: r_rad_sec
Cl33 = np.array(
                [
                [np.NaN, -0.1500, -0.1000, 0.0000, 0.1000, 0.1500],
                [0.2790, 1.0000, 1.0000, 1.0000, 1.0000, 1.0000],
                [0.2970, 35.0000, 30.0000, 1.0000, 30.0000, 35.0000],
                [0.5000, 5.0000, 5.0000, 1.0000, 5.0000, 5.0000]
                ]
              )
Cl33_trans = Cl33.transpose()
Cl33_interp = interpolate.interp2d(Cl33_trans[0,1:], Cl33_trans[1:,0], Cl33_trans[1:,1:])

#Roll moment coefficient due to flaps position
#Column 0: alpha_rad | Row 0: stall_hyst_norm 
Cl4 = np.array(
                [
                [np.NaN, 0.0000, 1.0000],
                [0.2790, 1.0000, 0.3000],
                [0.2970, 0.3000, 0.3000],
                [0.6110, -0.1000, -0.1000]
                ]
              )
Cl4_trans = Cl4.transpose()
Cl4_interp = interpolate.interp2d(Cl4_trans[0,1:], Cl4_trans[1:,0], Cl4_trans[1:,1:])

#Pitch moment coefficient due to qbar_psf
#Column 0: qbar_psf 
Cm1 = np.array(
                [
                [13.6000, 0.0900],
                [21.2000, 0.0400]
                ]
              )
Cm1_interp = interpolate.interp1d(Cm1[:,0], Cm1[:,1], bounds_error=False, fill_value=(Cm1[0,1], Cm1[-1,1]))

#Pitch moment coefficient due to alpha_deg
#Column 0: alpha_deg 
Cm2 = np.array(
                [
                [20.0000, 1.0000],
                [25.0000, 0.6000],
                [35.0000, 0.4000],
                [45.0000, 0.5000],
                [55.0000, 0.4000],
                [65.0000, 0.2000],
                [90.0000, 0.1000]
                ]
              )
Cm2_interp = interpolate.interp1d(Cm2[:,0], Cm2[:,1], bounds_error=False, fill_value=(Cm2[0,1], Cm2[-1,1]))
    
#Pitch moment coefficient due to elev_pos_rad and alpha_deg
#Column 0: elev_pos_rad | Row 0: alpha_deg
Cm5 = np.array(
                [
                [np.NaN, 18.0000, 25.0000, 35.0000, 45.0000, 55.0000, 65.0000, 90.0000],
                [-0.4900, 1.0000, 0.5000, 0.2000, 0.1000, 0.1000, 0.1000, 0.1000],
                [0.0000, 1.0000, 0.6000, 0.3000, 0.1500, 0.1000, 0.1000, 0.1000],
                [0.4000, 1.0000, 0.9000, 0.8000, 0.7000, 0.6000, 0.5000, 0.4000]
                ]
              )
Cm5_trans = Cm5.transpose()
Cm5_interp = interpolate.interp2d(Cm5_trans[0,1:], Cm5_trans[1:,0], Cm5_trans[1:,1:])

#Pitch moment coefficient due to flaps_pos_deg
#Column 0: flaps_pos_deg
Cm6 = np.array(
                [
                [0.0000, 0.0000],
                [10.0000, -0.0654],
                [20.0000, -0.0981],
                [30.0000, -0.1140]
                ]
              )
Cm6_interp = interpolate.interp1d(Cm6[:,0], Cm6[:,1], bounds_error=False, fill_value=(Cm6[0,1], Cm6[-1,1]))
    
#Yaw moment coefficient due to beta_rad 
#Column 0: beta_rad 
Cn1 = np.array(
                [
                [-0.3490, -0.0205],
                [0.0000, 0.0000],
                [0.3490, 0.0205]
                ]
              )
Cn1_interp = interpolate.interp1d(Cn1[:,0], Cn1[:,1], bounds_error=False, fill_value=(Cn1[0,1], Cn1[-1,1]))

#Yaw moment coefficient due to r_rad_sec
#Column 0: r_rad_sec | Row 0: alpha_rad 
Cn4 = np.array(
                [
                [np.NaN, 0.2790, 0.4000],
                [-15.0000, 0.0000, 0.0000],
                [-5.0000, 0.0000, 0.0000],
                [-3.0000, 0.0000, -0.2500],
                [-1.0000, 0.0000, 0.0000],
                [0.0000, 0.0000, 0.0000],
                [1.0000, 0.0000, 0.0000],
                [3.0000, 0.0000, 0.2500],
                [5.0000, 0.0000, 0.0000],
                [15.0000, 0.0000, 0.0000]
                ]
              )
Cn4_trans = Cn4.transpose()
Cn4_interp = interpolate.interp2d(Cn4_trans[0,1:], Cn4_trans[1:,0], Cn4_trans[1:,1:])

#Yaw moment coefficient due to alpha_rad and beta_rad
#Column 0: alpha_rad | Row 0: beta_rad 
Cn5 = np.array(
                [
                [np.NaN, -0.3500, 0.0000, 0.3500],
                [0.0000, -0.0216, -0.0216, -0.0216],
                [0.0700, -0.0390, -0.0786, -0.0390],
                [0.0940, -0.0250, -0.0504, -0.0250]
                ]
              )
Cn5_trans = Cn5.transpose()
Cn5_interp = interpolate.interp2d(Cn5_trans[0,1:], Cn5_trans[1:,0], Cn5_trans[1:,1:])

#Multiplier of thrust coefficient due to advance_ratio
#Column 0: advance_ratio
CT = np.array(
                [
                [0.0000, 0.0680],
                [0.1000, 0.0680],
                [0.2000, 0.0670],
                [0.3000, 0.0660],
                [0.4000, 0.0640],
                [0.5000, 0.0620],
                [0.6000, 0.0590],
                [0.7000, 0.0540],
                [0.8000, 0.0430],
                [0.9000, 0.0310],
                [1.0000, 0.0190],
                [1.1000, 0.0080],
                [1.2000, -0.0010],        
                [1.3000, -0.0080],        
                [1.4000, -0.0190],        
                [1.5000, -0.0290],
                [1.6000, -0.0400],
                [1.7000, -0.0500],
                [1.8000, -0.0570],
                [1.9000, -0.0610],
                [2.0000, -0.0640],
                [2.1000, -0.0660],
                [2.2000, -0.0670],
                [2.3000, -0.0680],
                [5.0000, -0.0680]
                ]
             )
CT_interp = interpolate.interp1d(CT[:,0], CT[:,1], bounds_error=False, fill_value=(CT[0,1], CT[-1,1]))

#Multiplier of power coefficient due to advance_ratio
#Column 0: advance_ratio
CP = np.array(
                [
                [0.0000, 0.0580],
                [0.1000, 0.0620],
                [0.2000, 0.0600],
                [0.3000, 0.0580],
                [0.4000, 0.0520],
                [0.5000, 0.0457],
                [0.6000, 0.0436],
                [0.7000, 0.0420],
                [0.8000, 0.0372],
                [0.9000, 0.0299],
                [1.0000, 0.0202],
                [1.1000, -0.0111],
                [1.2000, -0.0075],        
                [1.3000, -0.0111],        
                [1.4000, -0.0202],        
                [1.5000, -0.0280],
                [1.6000, -0.0346],
                [1.7000, -0.0389],
                [1.8000, -0.0421],
                [1.9000, -0.0436],
                [2.0000, -0.0445],
                [2.1000, -0.0445],
                [2.2000, -0.0442],
                [2.3000, -0.0431],
                [2.4000, -0.0421],
                [5.0000, -0.0413]
                ]
             )
CP_interp = interpolate.interp1d(CP[:,0], CP[:,1], bounds_error=False, fill_value=(CP[0,1], CP[-1,1]))

''' PARAMETERS CONVERSION '''
PROP_DIAM = in_to_m(PROP_DIAM_IN)

''' DRAG '''
def D0(qbar_psf):
    #Drag at null lift

    D1 = qbar_psf * SW_SQFT * 0.0270

    return D1

def DDf(qbar_psf, h_b_mac_ft, flaps_pos_deg):
    #Delta drag due to flaps position

    D2 = qbar_psf * SW_SQFT * kCDge_interp(h_b_mac_ft) * CD2_interp(flaps_pos_deg)

    return D2

def Dwbh(qbar_psf, h_b_mac_ft, alpha_rad, flaps_pos_deg):
    #Drag due to angle of attack and flaps position

    D3 = qbar_psf * SW_SQFT * kCDge_interp(h_b_mac_ft) * CD3_interp(alpha_rad, flaps_pos_deg)

    return D3

def DDe(qbar_psf, elev_pos_rad):
    #Delta drag due to elevators position

    D4 = qbar_psf * SW_SQFT * abs(elev_pos_rad) * 0.0000

    return D4

def Dbeta(qbar_psf, beta_rad):
    #Delta drag due to side-slip angle

    D5 = qbar_psf * SW_SQFT * abs(beta_rad) * 0.1500

    return D5

''' SIDE '''
def Yb(qbar_psf, beta_rad, flaps_pos_deg):
    #Side force due to side-slip angle
    
    Y1 = qbar_psf * SW_SQFT * CY1_interp(beta_rad, flaps_pos_deg)

    return Y1

def Ydr(qbar_psf, rudder_pos_rad):
    #Delta side force due to rudder position

    Y2 = qbar_psf * SW_SQFT * rudder_pos_rad * 0.1500

    return Y2

''' LIFT '''
def Lwbh(qbar_psf, h_b_mac_ft, alpha_rad, stall_hyst_norm):
    #Lift due to angle of attack and stall state

    L1 = qbar_psf * SW_SQFT * kCLge_interp(h_b_mac_ft) * CL1_interp(alpha_rad, stall_hyst_norm)

    return L1

def LDf(qbar_psf, h_b_mac_ft, flaps_pos_deg):
    #Delta lift due to flaps position

    L2 = qbar_psf * SW_SQFT * kCLge_interp(h_b_mac_ft) * CL2_interp(flaps_pos_deg)

    return L2

def LDe(qbar_psf, elev_pos_rad):
    #Delta lift due to elevators position

    L3 = qbar_psf * SW_SQFT * elev_pos_rad * 0.4300

    return L3

def Ladot(qbarUW_psf, alphadot_rad_sec, ci2vel):
    #Lift due to rate of change of angle of attack

    L4 = qbarUW_psf * SW_SQFT * alphadot_rad_sec * ci2vel * 1.7000

    return L4

def Lq(qbar_psf, q_rad_sec, ci2vel):
    #Lift due to pitch velocity

    L5 = qbar_psf * SW_SQFT * q_rad_sec * ci2vel * 3.9000

    return L5

''' ROLL '''
def lb(qbar_psf, beta_rad, alpha_rad):
    #Roll moment due to side-slip angle
    
    l1 = qbar_psf * SW_SQFT * BW_FT * beta_rad * -0.0920 * Cl1_interp(alpha_rad)

    return l1

def lp(qbar_psf, beta_rad, bi2vel, p_rad_sec):
    #Roll moment due to roll velocity

    l2 = qbar_psf * SW_SQFT * BW_FT * bi2vel * p_rad_sec * -0.4840

    return l2

def lr(qbar_psf, bi2vel, r_rad_sec, flaps_pos_deg, alpha_rad, stall_hyst_norm):
    #Roll moment due to yaw velocity

    if stall_hyst_norm:
        l3 = qbar_psf * SW_SQFT * BW_FT * bi2vel * r_rad_sec * Cl31_interp(flaps_pos_deg) * Cl32_interp(alpha_rad, r_rad_sec)

    else:
        l3 = qbar_psf * SW_SQFT * BW_FT * bi2vel * r_rad_sec * Cl31_interp(flaps_pos_deg) * Cl33_interp(alpha_rad, r_rad_sec)

    return l3

def lDa(qbar_psf, left_aileron_pos_rad, right_aileron_pos_rad, alpha_rad, stall_hyst_norm):
    #Delta roll moment due to ailerons position

    l4 = qbar_psf * SW_SQFT * BW_FT * averaged_ailerons(left_aileron_pos_rad, right_aileron_pos_rad) * 0.2290 * Cl4_interp(alpha_rad, stall_hyst_norm)

    return l4

def ldr(qbar_psf, rudder_pos_rad):
    #Delta roll moment due to rudder position

    l5 = qbar_psf * SW_SQFT * BW_FT * rudder_pos_rad * 0.0147

    return l5

''' PITCH '''
def m0(qbar_psf):
    #Pitch moment at null angle of attack

    m1 = qbar_psf * SW_SQFT * CBARW_FT * Cm1_interp(qbar_psf)

    return m1

def malpha(qbar_psf, alpha_deg, alpha_rad):
    #Pitch moment due to angle of attack

    m2 = qbar_psf * SW_SQFT * CBARW_FT * math.sin(alpha_rad) * -1.8000 * Cm2_interp(alpha_deg)

    return m2

def mq(qbar_psf, ci2vel, q_rad_sec):
    #Pitch moment due to pitch velocity

    m3 = qbar_psf * SW_SQFT * CBARW_FT * ci2vel * q_rad_sec * -12.4000

    return m3

def madot(qbarUW_psf, ci2vel, alphadot_rad_sec):
    #Pitch moment due to rate of change of angle of attack

    m4 = qbarUW_psf  * SW_SQFT * CBARW_FT * ci2vel * alphadot_rad_sec * -7.2700

    return m4

def mde(qbar_induced_psf, elev_pos_rad, alpha_deg):
    #Delta pitch moment due to elevator position

    m5 = qbar_induced_psf * SW_SQFT * CBARW_FT * elev_pos_rad * -1.2800 * Cm5_interp(elev_pos_rad, alpha_deg)

    return m5

def mdf(qbar_psf, flaps_pos_deg):
    #Delta pitch moment due to flaps position

    m6 = qbar_psf * SW_SQFT * CBARW_FT * Cm6_interp(flaps_pos_deg) * 0.7000

    return m6

''' YAW '''
def nb(qbar_psf, beta_rad):
    #Yaw moment due to side-slip angle

    n1 = qbar_psf * SW_SQFT * BW_FT * Cn1_interp(beta_rad)

    return n1

def nspw(qbar_propwash_psf):
    #Yaw moment due to spiraling propwash

    n2 = qbar_propwash_psf * SW_SQFT * BW_FT * -0.0500 * SPIRAL_PROPWASH_COEFF

    return n2

def nr(qbar_psf, bi2vel, r_rad_sec):
    #Yaw moment due to yaw velocity

    n3 = qbar_psf * SW_SQFT * BW_FT * bi2vel * r_rad_sec * -0.0937

    return n3

def nrf(qbar_psf, bi2vel, r_rad_sec, alpha_rad):
    #Yaw moment due to flat spin

    n4 = qbar_psf * SW_SQFT * BW_FT * bi2vel * Cn4_interp(r_rad_sec, alpha_rad)

    return n4

def nda(qbar_psf, left_aileron_pos_rad, right_aileron_pos_rad, alpha_rad, beta_rad):
    #Delta yaw moment due to aileron position

    n5 = qbar_psf * SW_SQFT * BW_FT * averaged_ailerons(left_aileron_pos_rad, right_aileron_pos_rad) * Cn5_interp(alpha_rad, beta_rad)

    return n5

def ndr(qbar_induced_psf, rudder_pos_rad):
    #Delta yaw moment due to rudder position

    n6 = qbar_induced_psf * SW_SQFT * BW_FT * rudder_pos_rad * -0.0645

    return n6

''' PROPULSION '''
def engine_thrust(advance_ratio, density, rps_prop):
    #Engine (160 HP) thrust

    T = CT_interp(advance_ratio) * density * (rps_prop ** 2) * (PROP_DIAM ** 4)

    return T

def engine_power(advance_ratio, density, rps_prop):
    #Engine (160 HP) power

    P = CP_interp(advance_ratio) * density * (rps_prop ** 3) * (PROP_DIAM ** 5)

    return P

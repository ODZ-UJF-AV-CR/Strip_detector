'''
 ******************************************************************************
 *                                                                            *
 *                        evolving systems consulting                         *
 *                         an esc Aerospace company                           *
 *                       https://www.esc-aerospace.com                        *
 *                                                                            *
 *                           ALL RIGHTS RESERVED                              *
 *                                                                            *
 ******************************************************************************

    Common PH32-related functions.

    $HeadURL: https://dev.esc-aerospace.com/svn/ene_ck_crreat/SW/utility/ph32lib.py $
    $Revision: 1292 $
    $Date: 2018-12-21 15:50:33 +0100 (pá, 21 12 2018) $
    $Author: escsro168 $

    Copyright 2018 esc Aerospace. All rights reserved.
'''

import DV
import struct
import math
import time

HW_VERSION_10 = 10
HW_VERSION_2030 = 20

HW_VERSION = HW_VERSION_2030
SHOW_FULL_DATA = True


def get_meas_time(timestamp, precision):
    tsSplit       = struct.unpack_from('<2I', timestamp)
    secTimestamp  = tsSplit[1]  # seconds timestamp (compatible with Unix time format)
    fracTimestamp = tsSplit[0] # fraction of a second (resolution 2^32)
    fracSec       = int(round((fracTimestamp / 4294967296), precision) * (10**precision))
    
    measTime = time.gmtime(secTimestamp)
    return [measTime, fracSec, secTimestamp, fracTimestamp]

def load_config_from_file(filename):
    print("filename=", filename)
    with open(filename, 'rb') as f:
        config = f.read()
        assert len(config) == DV.T_DETECTOR_CONFIGURATION_REQUIRED_BYTES_FOR_ACN_ENCODING
    return config
    
def reverse_strips(strip_data):
    for i in range(16):
        tmp1 = strip_data[i]
        strip_data[i] = strip_data[31 - i]
        strip_data[31 - i] = tmp1

def get_strip_value_len(strip_val):
    places = 0
    if strip_val < 0:
        places = 2
    elif strip_val < 10:
        places = 1
    elif strip_val < 100:
        places = 2
    elif strip_val < 1000:
        places = 3
    elif strip_val < 10000:
        places = 4
    else:
        places = 5
    return places
    
def strips_print_len(value_strip_map, m1_data, m2_data):
    places = 0
    
    for i in range(len(m1_data)):
        places = get_strip_value_len(m1_data[i])
        if value_strip_map[i] < places:
            value_strip_map[i] = places
            
    for i in range(len(m2_data)):
        places = get_strip_value_len(m2_data[i])
        if value_strip_map[i+32] < places:
            value_strip_map[i+32] = places
    
    return
    
def show_strip_data(strip_hit_count):
    if strip_hit_count == 0:       # No hit
        return "_"
    elif strip_hit_count == -1:    # Measurement did not start
        return "x"
    elif strip_hit_count == 65534: # Saturation
        return "s"
    elif strip_hit_count > 0:      # Hit
        #return "|"
        if strip_hit_count < 10:
            return str(strip_hit_count)
        else:
            return "o"
    else:
        return " "
        
def show_strip_data_full(strip_hit_count, places):
    if strip_hit_count == 0:
        val = "_|"
        val = val.rjust(places + 1,'_')
    else:
        val = "%d|" %(strip_hit_count)
        val = val.rjust(places + 1,' ')
    
    return val
        
def show_sensor(all_strips_hit_count):
    for i in range(len(all_strips_hit_count)):
        # char = show_strip_data(all_strips_hit_count[i])
        char = show_strip_data_full(all_strips_hit_count[i])
        print(char, end='', flush=True)
        
def show_sensor_aligned(all_strips_hit_count, strip_data_len_map):
    for i in range(len(all_strips_hit_count)):
        if SHOW_FULL_DATA != True:
            char = show_strip_data(all_strips_hit_count[i])
        else:
            char = show_strip_data_full(all_strips_hit_count[i], strip_data_len_map[i])
        print(char, end='', flush=True)
        
def unpack_detectors(array_of_bytestrings):
    return [[0xfffe - i for i in struct.unpack('<32H', bytes)] for bytes in array_of_bytestrings]

def hits_in_layer(m1_data, m2_data):
    lay_hits = 0
    for i in range(len(m1_data)):
        if m1_data[i] > 0 and m1_data[i] < 65535:
            lay_hits = lay_hits + m1_data[i]
    for i in range(len(m2_data)):
        if m2_data[i] > 0 and m2_data[i] < 65535:
            lay_hits = lay_hits + m2_data[i]
    return lay_hits

#number of hits without errors and saturation
def hits_in_layer_2(m1_data, m2_data):
    lay_hits = 0
    for i in range(len(m1_data)):
        if m1_data[i] > 0 and m1_data[i] < 65534:
            lay_hits = lay_hits + m1_data[i]
    for i in range(len(m2_data)):
        if m2_data[i] > 0 and m2_data[i] < 65534:
            lay_hits = lay_hits + m2_data[i]
    return lay_hits
    
# number of real hits 
def hits_in_layer3(m1_data, m2_data):
    lay_hits = 0
    for i in range(len(m1_data)):
        if m1_data[i] > 0 and m1_data[i] < 65535:
            lay_hits = lay_hits + 1
    for i in range(len(m2_data)):
        if m2_data[i] > 0 and m2_data[i] < 65535:
            lay_hits = lay_hits + 1
    return lay_hits
    
def find_hit_in_layer(m1_data, m2_data):
    zero_detected = False
    hit_detected = False
    hit_index = -1
    
    for i in range(len(m1_data)):
        if m1_data[i] == 0 or m1_data[i] == -1:
            zero_detected = True
        if m1_data[i] > 0 and m1_data[i] < 65535:
            #Check for a gap between hits (invalid configuration)
            if (hit_detected == True) and (zero_detected == True):
                return -1
            hit_detected = True
            zero_detected = False
            hit_index = i
    
    #simulate a gap (zero) between chips
    zero_detected = True

    for i in range(len(m2_data)):
        if m2_data[i] == 0 or m2_data[i] == -1:
            zero_detected = True
        if m2_data[i] > 0 and m2_data[i] < 65535:
            #Check for a gap between hits (invalid configuration)
            if (hit_detected == True) and (zero_detected == True):
                return -1
            hit_detected = True
            zero_detected = False
            hit_index = i + 32
    
    return hit_index

def find_hit_position(m1_data, m2_data):
    stripWidth = 250
    edgeWidth = 1165
    
    hitIdx = find_hit_in_layer(m1_data, m2_data)
    if hitIdx < 0:
        return -1
    
    # calculate distance from the left edge in micrometers
    dist = (hitIdx * stripWidth) + (stripWidth / 2)
    
    if hitIdx > 31:
        data = m2_data
    else:
        data = m1_data
    # Check whether the next strip has also been hit
    if (hitIdx >=0 and hitIdx <= 30) or (hitIdx >=32 and hitIdx <= 62):
        if hitIdx > 31:
            nextStripHitCnt = data[hitIdx - 32 + 1]
        else:
            nextStripHitCnt = data[hitIdx + 1]
        if nextStripHitCnt > 0:
            dist = dist + (stripWidth / 2) # Modify distance (in the middle of the strips)

    # Add up the an inactive area width between chips if the hit has been on the second chip
    if hitIdx > 31:
        dist = dist + edgeWidth*2

    return dist
    
def calc_hit_angle(top_layer_m1_data, top_layer_m2_data, bot_layer_m1_data, bot_layer_m2_data):
    if HW_VERSION == HW_VERSION_10:
        # HW version 10
        layerHeight = 2*6350 + 2*1300 # two distances + two PCBs
    elif HW_VERSION == HW_VERSION_2030:
        # HW version 20 & 30
        layerHeight = 2*2000 + 2*1300 # two distances + two PCBs
    
    ltDist = find_hit_position(top_layer_m1_data, top_layer_m2_data)
    lbDist = find_hit_position(bot_layer_m1_data, bot_layer_m2_data)
    
    if (ltDist < 0) or (lbDist < 0):
        return -1 #-1 deg cannot be valid angle due to field of view

    deltaDist = ltDist - lbDist
    
    return math.degrees(math.atan2(layerHeight, deltaDist))

def reorder_data(data):
    #################################################################################
    # Data reordering
    #################################################################################
    
    if HW_VERSION == HW_VERSION_10:
        # Layer 4 ||
        # No reversing necessary
        # Layer 3 =
        # No reversing necessary
        # Layer 2 || (mirrored)
        reverse_strips(data[3])
        reverse_strips(data[2])
        # Layer 1 = (mirrored)
        reverse_strips(data[1])
        reverse_strips(data[0])
    elif HW_VERSION == HW_VERSION_2030:
        # Layer 4 =
        # No reversing necessary
        # Layer 3 || (mirrored)
        reverse_strips(data[5])
        reverse_strips(data[4])
        # Layer 2 = (mirrored)
        reverse_strips(data[3])
        reverse_strips(data[2])
        # Layer 1 || 
        # No reversing necessary
    else:
        print("UNKNOWN WH VERSION!")

def print_layer_hist(data, statData):
    layHits = [0,0,0,0]
    layHits[3] = hits_in_layer_2(data[6], data[7])
    # layHits[2] = hits_in_layer_2(data[4], data[5])
    # layHits[1] = hits_in_layer_2(data[3], data[2])
    layHits[0] = hits_in_layer_2(data[1], data[0])
    
    statData[3] += layHits[3]
    # statData[2] += layHits[2]
    # statData[1] += layHits[1]
    statData[0] += layHits[0]
    
    maxHitsStat = max(statData)
    maxFlagStat = [' ',' ',' ',' ']
    for i in range(4):
        if statData[i] == maxHitsStat:
            maxFlagStat[i] = '<'
    
    maxHitsCurr = max(layHits)
    maxFlagCurr = [' ',' ',' ',' ']
    for i in range(4):
        if layHits[i] == maxHitsCurr:
            maxFlagCurr[i] = '<'
            
    print("L4 = %5d %s (+%d %s)" %(statData[3], maxFlagStat[3], layHits[3], maxFlagCurr[3]))
    # print("L3 = %5d %s (+%d %s)" %(statData[2], maxFlagStat[2], layHits[2], maxFlagCurr[2]))
    # print("L2 = %5d %s (+%d %s)" %(statData[1], maxFlagStat[1], layHits[1], maxFlagCurr[1]))
    print("L1 = %5d %s (+%d %s)" %(statData[0], maxFlagStat[0], layHits[0], maxFlagCurr[0]))
    return

def print_chip_hist(data, statDataChip):
    chipHits = [0,0,0,0,0,0,0,0]
    for i in range(8):
        chipHits[i] = hits_in_layer_2(data[i], [])
        statDataChip[i] += chipHits[i]
    
    
    # maxHitsStat = max(statData)
    # maxFlagStat = [' ',' ',' ',' ']
    # for i in range(4):
        # if statData[i] == maxHitsStat:
            # maxFlagStat[i] = '<'
    
    # maxHitsCurr = max(layHits)
    # maxFlagCurr = [' ',' ',' ',' ']
    # for i in range(4):
        # if layHits[i] == maxHitsCurr:
            # maxFlagCurr[i] = '<'
            
    print("L4 M1 = %5d (+%d) | M2 = %5d (+%d)" %(statDataChip[6], chipHits[6], statDataChip[7], chipHits[7]))
    print("L1 M1 = %5d (+%d) | M2 = %5d (+%d)" %(statDataChip[0], chipHits[0], statDataChip[1], chipHits[1]))
    
    # for i in range(4):
        # print("L%d M1 = %5d (+%d) | M2 = %5d (+%d)" %(4-i, statDataChip[(4 - i)*2 - 2], chipHits[(4 - i)*2 - 2], statDataChip[(4 - i)*2 - 1], chipHits[(4 - i)*2 - 1]))


    return
    
def print_data(data):
    accumulated = data

    #################################################################################
    # Total number of hits calculation
    #################################################################################
    tot_hits = 0
    for i in range(len(data)):
        for j in range(len(data[i])):
            if data[i][j] > 0 and data[i][j] < 65534:
                # tot_hits = tot_hits + data[i][j]
                tot_hits += 1

    print("TOTAL HITS =", str(tot_hits))
    
    #################################################################################
    # Particle direction calculation
    #################################################################################
    l4Hits = hits_in_layer3(accumulated[6], accumulated[7])
    l3Hits = hits_in_layer3(accumulated[5], accumulated[4])
    l2Hits = hits_in_layer3(accumulated[3], accumulated[2])
    l1Hits = hits_in_layer3(accumulated[0], accumulated[1])
    
    disableHitLimit = False
    
    if disableHitLimit == True:
        # Limit check is disabled because the layHitLimit variable is higher than maximum detector sum
        layHitLimit = 4194240 # 64 strips * 65535 (strip max value)
    else:
        # layHitLimit = 2
        layHitLimit = 3
        
    if ((l4Hits > layHitLimit) or (l3Hits > layHitLimit) or (l2Hits > layHitLimit) or (l1Hits > layHitLimit)):
        print("DIRECTION CANNOT BE CALCULATED: TOO MANY HITS")
    else:
        if HW_VERSION == HW_VERSION_10:
            angleXRes = calc_hit_angle(accumulated[6], accumulated[7], accumulated[3], accumulated[2])
            angleYRes = calc_hit_angle(accumulated[4], accumulated[5], accumulated[1], accumulated[0])
            
            angleX = angleXRes
            angleY = 180 - angleYRes # Correction for Y axis
            
        elif HW_VERSION == HW_VERSION_2030:
            angleXRes = calc_hit_angle(accumulated[5], accumulated[4], accumulated[0], accumulated[1])
            angleYRes = calc_hit_angle(accumulated[6], accumulated[7], accumulated[3], accumulated[2])
            
            angleX = angleXRes
            angleY = 180 - angleYRes # Correction for Y axis
        else:
            print("UNKNOWN WH VERSION!")
        
        if (angleXRes < 0) or (angleYRes < 0):
            print("DIRECTION CANNOT BE CALCULATED: INVALID DATA")
        else:
            print("DIRECTION X =", round(angleX), "deg")
            print("DIRECTION Y =", round(angleY), "deg")
    
    #################################################################################
    # Data visualization
    #################################################################################
    
    strip_data_len = [0] * 64
    if HW_VERSION == HW_VERSION_10:
        strips_print_len(strip_data_len, accumulated[6], accumulated[7])
        strips_print_len(strip_data_len, accumulated[4], accumulated[5])
        strips_print_len(strip_data_len, accumulated[3], accumulated[2])
        strips_print_len(strip_data_len, accumulated[1], accumulated[0])
        
        # Layer 4 ||
        show_sensor(accumulated[6])
        print(" ", end='')
        show_sensor(accumulated[7])
        print("")
        
        # Layer 3 =
        show_sensor(accumulated[4])
        print(" ", end='')
        show_sensor(accumulated[5])
        print("")
        
        # Layer 2 || (mirrored)
        show_sensor(accumulated[3])
        print(" ", end='')
        show_sensor(accumulated[2])
        print("")
        
        # Layer 1 = (mirrored)
        show_sensor(accumulated[1])
        print(" ", end='')
        show_sensor(accumulated[0])
        print("", flush=True)
    elif HW_VERSION == HW_VERSION_2030:
        strips_print_len(strip_data_len, accumulated[6], accumulated[7])
        strips_print_len(strip_data_len, accumulated[5], accumulated[4])
        strips_print_len(strip_data_len, accumulated[3], accumulated[2])
        strips_print_len(strip_data_len, accumulated[0], accumulated[1])
        
        # Layer 4 =
        show_sensor_aligned(accumulated[6], strip_data_len)
        print("  ", end='')
        show_sensor_aligned(accumulated[7], strip_data_len[32:])
        print("")
        
        # Layer 3 || (mirrored)
        show_sensor_aligned(accumulated[5], strip_data_len)
        print("  ", end='')
        show_sensor_aligned(accumulated[4], strip_data_len[32:])
        print("")
        
        # Layer 2 = (mirrored)
        show_sensor_aligned(accumulated[3], strip_data_len)
        print("  ", end='')
        show_sensor_aligned(accumulated[2], strip_data_len[32:])
        print("")
        
        # Layer 1 ||
        show_sensor_aligned(accumulated[0], strip_data_len)
        print("  ", end='')
        show_sensor_aligned(accumulated[1], strip_data_len[32:])
        print("", flush=True)

    else:
        print("UNKNOWN WH VERSION!")
    print("")

def print_housekeeping(hk_tm):
    systimeBin = hk_tm.packetDataField.tmSourceData.tm_3_25_HkReport.systemTime.GetPyString()
    precision     = 9
    tsSplit       = struct.unpack_from('<2I', systimeBin)
    secTimestamp  = tsSplit[1]  # seconds timestamp (compatible with Unix time format)
    fracTimestamp = tsSplit[0] # fraction of a second (resolution 2^32)
    fracSec       = int((fracTimestamp / 4294967296) * (10**precision))
    sysTime = time.gmtime(secTimestamp)
    
    print("---------------------")
    print(" Housekeeping report ")
    print("---------------------")
    print('System Time         =', time.strftime("%H:%M:%S.", sysTime) + '{frac:0{pres}}'.format(frac=fracSec, pres=precision) + time.strftime(" %d/%m/%Y UTC", sysTime))
    print("ECU SW Version      =", hk_tm.packetDataField.tmSourceData.tm_3_25_HkReport.creecuSwVersion.Get())
    print("FPG SW Version      =", '0x{:08X}'.format(hk_tm.packetDataField.tmSourceData.tm_3_25_HkReport.crefpgSwVersion.Get()))
    print("CREFPG 1 Enabled    =", hk_tm.packetDataField.tmSourceData.tm_3_25_HkReport.crefpg1Enabled.Get())
    print("CREFPG 2 Enabled    =", hk_tm.packetDataField.tmSourceData.tm_3_25_HkReport.crefpg2Enabled.Get())
    print("CREFPG 3 Enabled    =", hk_tm.packetDataField.tmSourceData.tm_3_25_HkReport.crefpg3Enabled.Get())
    print("Time Sync Method    =", {'0': 'Not Synced (0)', '1': 'TC Synced (1)', '2': 'GNSS Synced (2)'}[str(hk_tm.packetDataField.tmSourceData.tm_3_25_HkReport.timeSyncMethod.Get())])
    print("GNSS Locked         =", hk_tm.packetDataField.tmSourceData.tm_3_25_HkReport.gnssLocked.Get())
    print("Measurement Running =", hk_tm.packetDataField.tmSourceData.tm_3_25_HkReport.measRunning.Get())
    print("Storing Enabled     =", hk_tm.packetDataField.tmSourceData.tm_3_25_HkReport.measStoringEnabled.Get())
    print("Det. 1 Reinit Count =", hk_tm.packetDataField.tmSourceData.tm_3_25_HkReport.det1ReinitCnt.Get())
    print("Det. 2 Reinit Count =", hk_tm.packetDataField.tmSourceData.tm_3_25_HkReport.det2ReinitCnt.Get())
    print("Det. 3 Reinit Count =", hk_tm.packetDataField.tmSourceData.tm_3_25_HkReport.det3ReinitCnt.Get())
    print("Stored Meas. Count  =", hk_tm.packetDataField.tmSourceData.tm_3_25_HkReport.storedMeasCnt.Get())
    
def print_hitglobal(hitglb_status):
    chips = []
    if hitglb_status != 0:
        if hitglb_status & 0x80:
            chips.append('4x2')
        if hitglb_status & 0x40:
            chips.append('4x1')
        if hitglb_status & 0x20:
            chips.append('3x2')
        if hitglb_status & 0x10:
            chips.append('3x1')
        if hitglb_status & 0x08:
            chips.append('2x2')
        if hitglb_status & 0x04:
            chips.append('2x1')
        if hitglb_status & 0x02:
            chips.append('1x2')
        if hitglb_status & 0x01:
            chips.append('1x1')
    else:
        chips.append('n/a')
        
    print("Hit Global=", ' | '.join(chips))

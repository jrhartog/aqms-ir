import numpy as np
import logging

try:
    from obspy.signal.invsim import paz_to_freq_resp
except:
    from obspy.signal.invsim import pazToFreqResp as paz_to_freq_resp
try:
    from obspy.signal.invsim import paz_2_amplitude_value_of_freq_resp
except:
    from obspy.signal.invsim import paz2AmpValueOfFreqResp as paz_2_amplitude_value_of_freq_resp

def compute_corners(amplitude,frequency):
    """
        :param amplitude: amplitude spectrum of time series
        :type amplitude: array of floats
        :param frequency: frequency values of amplitude spectrum
        :type frequency: array of floats
        :returns: high-pass and low-pass cutoff frequency (floats)
        :raises: ValueError
    """
    # check to see amplitude and frequency arrays have the same length
    if len(amplitude) != len(frequency):
        raise ValueError("input arrays are not the same length")
    
    CONST = 1.0/np.sqrt(2.0)
    f_hp = 0
    f_lp = 200

    magnitude = np.abs(amplitude)
    # find maximum amplitude index 
    a_max = np.max(magnitude)
    i_max = np.argmax(magnitude)

    # find the low frequency cut off (high-pass)
    if i_max == 0:        
        # maximum abs amplitude at DC
        f_hp = 0
    else:
        # find where abs amplitude < 1/sqrt(2)
        for i in range(i_max,0,-1):
            if magnitude[i] < CONST: 
                # linear interpolation
                f_hp = frequency[i] + (CONST-magnitude[i]) * ( (frequency[i-1]-frequency[i])/(magnitude[i-1]-magnitude[i]) )
                break

    # find the high frequency cut off (low-pass)
    f_lp = frequency[-1]
    for i in range(i_max,len(frequency)):
        if magnitude[i] < CONST:
            # linear interpolation
            f_lp = frequency[i-1] + (magnitude[i-1]-CONST) * ( (frequency[i]-frequency[i-1])/(magnitude[i]-magnitude[i-1]) )
            break
    return f_hp, f_lp

def natural_frequency_and_damping(poles,f_hp,f_lp,sensor_type="VEL"):
    """
        :param poles: complex conjugate poles, conjugate pair assumed to be sequential
        :type poles: array of floats
        :param f_hp: high-pass cutof frequency in Hz
        :type f_hp: float
        :param f_lp: high-pass cutof frequency in Hz
        :type f_lp: float
        :param sensor_type:VEL,ACC, default=VEL
        :type sensor_type: string
        :returns: natural frequency and damping factor (floats)
    """

    # find any complex conjugate pole pairs, to find candidate fs and damp
    fs_candidate = []
    b_candidate = []
    for i in range(len(poles)):
        p1 = poles[i]
        for j in range(i+1,len(poles)):
            p2 = poles[j]
            if p1.real == p2.real and p1.imag == -1*p2.imag and p1.real != 0.:
                # a conjugate pair
                omega_s = np.abs(p1)
                fs_candidate.append(omega_s/(2*np.pi))
                b_candidate.append(-1*p1.real/omega_s)
                logging.debug("candidate conjugate poles: {} and {}, ws={}, fs={}, b={} (compare to {}-{})".format(p1,p2,omega_s,omega_s/(2*np.pi),-1*p1.real/omega_s,f_hp,f_lp))
                break

    if len(fs_candidate) == 0:
        # don't know how to do natural freq and damping w/o conj. pole pairs
        return 0., 0.

    # pick the candidate that is close to a corner frequency
    # for velocity/displacement pick the one close to f_hp, acceleration close to f_lp
    if sensor_type == "VEL":
        logging.debug( ("BB/SP sensor_type: {}").format(sensor_type) )
        df = np.abs( np.subtract(fs_candidate, f_hp) ) 
    else:
        logging.debug( ("SM sensor_type: {}").format(sensor_type) )
        df = np.abs( np.subtract(fs_candidate, f_lp) )
    i_min = np.argmin(df)
    fn = fs_candidate[i_min]
    damp = b_candidate[i_min]
    return fn, damp

def simple_response(sample_rate,response):
    """ 
        Given the obspy ResponseStages, calculate the simple response.
        i.e. the natural frequency, damping factor, low corner, high corner, and overall gain
    """
    EPSILON = 5e-02 # tolerance for normalized amplitude of a pole-zero stage being off from 1.0
    NFREQ = 2048 # number of frequency points to calculate amplitude spectrum for.
    delta_t = 1.0/sample_rate 
    poles = []
    zeros = []

    # take the normalization frequency from the InstrumentSensitivity 
    normalization_frequency = response.instrument_sensitivity.frequency
    signal_input_units = response.instrument_sensitivity.input_units

    # Gather all the poles and zeros, and the stage gains.
    total_gain = 1
    for stage in response.response_stages:
        if hasattr(stage, "stage_gain"):
            stage_gain = stage.stage_gain
            if hasattr(stage,"zeros"):
                zeros.extend(stage.zeros)
            if hasattr(stage,"poles"):
                poles.extend(stage.poles)
                # check if normalization factor is correct 
                paz = { "poles" : stage.poles, "zeros" : stage.zeros, "gain" : stage.normalization_factor}
                calculated_amplitude = paz_2_amplitude_value_of_freq_resp(paz, stage.normalization_frequency)
                if np.abs(calculated_amplitude - 1.0) > EPSILON:
                    logging.warning("Warning: normalized amplitude at normalization frequency  is {}, i.e. {:6.3f}% from 1,\
                           using calculated gain value {:5.2f} vs {:5.2f} instead".\
                           format(calculated_amplitude, 100*(calculated_amplitude-1)/1,calculated_amplitude*stage.stage_gain, stage.stage_gain))
                    stage_gain = calculated_amplitude * stage.stage_gain
            total_gain = total_gain*stage_gain         

    # log a warning if the total_gain is not similar to the reported instrument_sensitivity
    if np.abs( (total_gain - response.instrument_sensitivity.value)/response.instrument_sensitivity.value) > EPSILON:
        logging.warning("Warning: Reported sensitivity: {:5.2f}, \
                        Calculated sensitivity: {:5.2f}". \
              format(response.instrument_sensitivity.value, total_gain))

    #  calculate overall normalization factor at normalization frequency
    paz = { "poles" : poles, "zeros" : zeros, "gain" : 1.0 }
    calculated_amplitude = paz_2_amplitude_value_of_freq_resp(paz, normalization_frequency)
    normalization_factor = 1.0/calculated_amplitude

    # calculate the normalized frequency spectrum at NFREQ frequency points
    amplitude, frequency = paz_to_freq_resp(poles,zeros,normalization_factor,delta_t,2*NFREQ,freq=True)

    # determine the high and low frequency corners from the amplitude spectrum
    logging.debug("Determining frequency corners")
    f_hp, f_lp = compute_corners(amplitude,frequency)
    logging.debug( ("f_hp: {}, f_lp: {}").format(f_hp,f_lp) )

    # velocity transducer or acceleration?
    if signal_input_units == "M/S" or signal_input_units == "M":
        sensor_type = "VEL"
    else:
        sensor_type = "ACC"

    # try to determine natural frequency and damping factor from poles and corners
    logging.debug("Determining natural frequency and damping factor")
    natural_frequency, damping = natural_frequency_and_damping(poles, f_hp, f_lp, sensor_type=sensor_type)
    logging.debug( ("fn: {}, damp: {}").format(natural_frequency, damping) )
    
    # some sanity checks, limit f_lp to 40% of Nyquist, f_hp must be <= f_lp
    if f_lp > 0.4*sample_rate:
        f_lp = 0.4*sample_rate
    if f_hp > f_lp:
        f_hp = f_lp

    return natural_frequency, damping, f_hp, f_lp, total_gain

def get_cliplevel(sensor, sensor_sn, logger, logger_sn, gain):
    """
        Tries to determine the instrument cliplevel in counts based on
        the sensor/logger combination. Sometimes the maximum number of counts
        out is the maximum counts of the digitizer, sometimes, it is the
        due to clipping of the sensor and sometimes those two quantities are 
        the same (when max Volts out of the sensor matches the max Volts in 
        of the logger).

        @params[string]: sensor
    """

    cliplevel = -1   

    logging.debug("In get_cliplevel: {},{},{},{},{}\n".format(sensor, sensor_sn, logger, logger_sn, gain))
    if sensor and not logger:
        logging.debug("have sensor but not logger: {},{},{},{}\n".format(sensor, sensor_sn, logger, logger_sn))
        # do not have any info about logger, this can happen, for example:
        # SIS dataless instrument identifier is sensor_model,sensor_description,sensor_type
        # let's assume this is the provenance of the StationXML (SIS dataless->IRIS->stationXML)
        if "320" in sensor:
            # IDS packages, were 2g
            cliplevel = gain * 2 * 9.8
        elif "CMG-5TD" in sensor or "CMG-5T" in sensor:
            # 4g, except for a few, but can't tell.
            cliplevel = gain * 4 * 9.8
        elif "EPISENSOR DECK" in sensor:
            # most internal episensors of our were set to 2g
            cliplevel = gain * 2 * 9.8
        elif "EPISENSOR" in sensor:
            # assume the rest is 4g
            cliplevel = gain * 4 * 9.8
        elif "RT147" in sensor:
            # PNSN's were 4g
            cliplevel = gain * 4 * 9.8
        elif "TITAN" in sensor or "Titan" in sensor:
            cliplevel = gain * 4 * 9.8
        elif "FBA" in sensor:
            cliplevel = gain * 9.8
        elif "GEOSIG-AC-63" in sensor:
            cliplevel = gain * 3 * 9.8
        elif "CMG-40T" in sensor or "CMG40T" in sensor:
            # 1.25 cm/s
            cliplevel = gain * 0.0125
        elif "CMG-3T" in sensor:
            # 0.67 cm/s
            cliplevel = gain * 0.0067
        elif "CMG-3ESP" in sensor:
            # 0.50 cm/s
            cliplevel = gain * 0.0050
        elif "TRILLIUM COMPACT" in sensor or "CASCADIA" in sensor:
            # 2.6 cm/s
            cliplevel = gain * 0.0260
        elif "TRILLIUM" in sensor or "TR240" in sensor or "TR120" in sensor or "T120PA" in sensor:
            # 1.66 cm/s
            cliplevel = gain * 0.0166
        elif "STS-2" in sensor:
            cliplevel = gain * 0.0120
        elif "CMG-6T" in sensor or "CMG-EDU" in sensor:
            cliplevel = gain * 0.00417
        elif "HS-1-LT" in sensor:
            cliplevel = gain * 0.001
        elif "L-4C" in sensor:
            cliplevel = gain * 0.001
        elif "L-22" in sensor:
            cliplevel = gain * 0.001
        elif "SS-1" in sensor:
            cliplevel = gain * 0.001
        elif "S-13" in sensor:
            cliplevel = gain * 0.001
        return cliplevel

    # when we do have logger model name, do the following logic:
    logging.debug("have sensor and logger: {},{},{},{}\n".format(sensor, sensor_sn, logger, logger_sn))

    # national instruments earthworm data loggers, use 2048
    if "Wrm" in logger or "Gusan" in logger or "Ralph" in logger or \
       "Analog" in logger or "EARTHWORM NI" in logger or "LEGACY" in logger:
        cliplevel = 2048
        logging.debug("EW logger: {}, cliplevel: {}\n".format(logger,cliplevel))

    # community project earthworm digitizer, use 16384 except for Rim Village
    elif "PSN" in logger:
        if "rv" in logger:
            cliplevel = 8192.
        else:
            cliplevel = 16384
        logging.debug("PSN logger: {}, cliplevel: {}\n".format(logger,cliplevel))

    # Gener datalogger, something digital, with a broadband attached probably
    elif "Gener" in logger:
        cliplevel = gain * 0.0065
        logging.debug("Gener logger: {}, cliplevel: {}\n".format(logger,cliplevel))

    # Cascades-16S with short-period, assume clipping is due to sensor, assume something small
    elif "C16S" in logger or "CASCADES-16S" in logger:
        cliplevel = gain * 0.0001
        if cliplevel > 32768.:
            cliplevel = 32768.
        logging.debug("C16S logger: {}, cliplevel: {}\n".format(logger,cliplevel))

    # NetQuakes are all set to 3g
    elif "NQ" in logger or "NETQUAKE" in logger:
        cliplevel = gain * 3 * 9.8
        logging.debug("NQ logger: {}, cliplevel: {}\n".format(logger,cliplevel))

    # IDS strong-motion were all 2g
    elif "IDS" in logger: 
        if "320" in sensor:
            cliplevel = gain * 2 * 9.8
        elif "G40T_60" in sensor or "CMG-40T" in sensor:
            # 1.25 cm/s
            cliplevel = gain * 0.0125
        elif "PMD" in sensor:
            # 0.65 cm/s (just a guess)
            cliplevel = gain * 0.0065
        logging.debug("IDS logger: {}, cliplevel: {}\n".format(logger,cliplevel))

    # Our CMG-5TD packages were supposed to be 4g, but some were set to 8g
    elif "G5TD" in logger or "CMG-5TD" in sensor:
        cliplevel = gain * 4 * 9.8
        if logger_sn in ["D838", "D833", "D820", "D826", "D817", "D825", "D810"]:
            cliplevel = 2 * cliplevel
        logging.debug("G5TD logger: {}, cliplevel: {}\n".format(logger,cliplevel))

    # CMG-6TD clips at 4.17 cm/s
    elif "G6TD" in logger or "CMG-6T" in sensor:
        cliplevel = gain * 0.00417
        logging.debug("G6TD logger: {}, cliplevel: {}\n".format(logger,cliplevel))

    # CMG-EDU like 6TD clips at 4.17 cm/s
    elif "GEDU" in logger or "CMG-EDU" in sensor:
        cliplevel = gain * 0.00417
        logging.debug("GEDU logger: {}, cliplevel: {}\n".format(logger,cliplevel))

    # Our Titans in TitanSMAs are all set to 4g
    elif "TITAN" in logger:
        cliplevel = gain * 4 * 9.8
        logging.debug("TITANsma logger: {}, cliplevel: {}\n".format(logger,cliplevel))

    # same with the ones inside the Trillium Cascadia
    elif "CENT" in logger or "CENTAUR" in logger:
        if "TITAN" in sensor:
            cliplevel = gain * 4 * 9.8
        elif "TRCOM" in sensor or "TRILLIUM COMPACT PH" in sensor:
            # 2.6 cm/s
            cliplevel = gain * 0.0260 
        logging.debug("CENTAUR logger: {}, cliplevel: {}\n".format(logger,cliplevel))

    # ES-T attached to or inside K2s etc. were usually set to 2g with a few exceptions.
    elif "K2" in logger or "Etna" in logger or "MAK" in logger or "GRAN" in logger:
        if "ES" in sensor or "SBEPI" in sensor or "FBA23" in sensor or "EPISENSOR" in sensor or "FBA-23" in sensor:
            cliplevel = gain * 2 * 9.8
            if logger_sn == "2147":
                cliplevel = 2*cliplevel
        elif "L4" in sensor or "L4C" in sensor or "S13" in sensor or "L-4C" in sensor or "S-13" in sensor:
            cliplevel = gain * 0.0001
        elif "GEDU" in sensor or "CMG-EDU" in sensor:
            cliplevel = gain * 0.00417 
        elif "PMD" in sensor:
            # 0.65 cm/s no idea
            cliplevel = gain * 0.0065
        logging.debug("K2 logger: {}, cliplevel: {}\n".format(logger,cliplevel))

    # ES-T attached to or inside Basalts/Obsidians were usually set to 4g with a few exceptions.
    elif "ROCK" in logger or "OBSID" in logger or "BASALT" in logger:
        if "ES" in sensor:
            cliplevel = gain * 4 * 9.8
            if logger_sn in ["1597", "1598", "1599", "1600", "1601"]:
                # hanford loggers with internal Episensors set to 2g
                cliplevel = 0.5*cliplevel
        elif "L4" in sensor or "L4C" in sensor or "S13" in sensor or "L-4C" in sensor or "S-13" in sensor:
            cliplevel = gain * 0.0001
        logging.debug("ROCK logger: {}, cliplevel: {}\n".format(logger,cliplevel))

    # Old refteks
    elif "72A" in logger:
        if "ES" in sensor or "EPISENSOR" in sensor:
            cliplevel = gain * 2 * 9.8
        elif "FBA" in sensor:
            cliplevel = gain * 1 * 9.8
        elif "L22" in sensor:
            cliplevel = gain * 0.0001
        elif "G40T_60" in sensor or "CMG-40T" in sensor or "CMG40T" in sensor:
            cliplevel = 0.0125
        elif "G3TNSN" in sensor or "CMG-3T/NSN" in sensor:
            cliplevel = 0.0067
        elif "G3T" in sensor or "CMG-3T" in sensor or "GT3134" in sensor:
            cliplevel = 0.0067
        logging.debug("RefTek logger: {}, cliplevel: {}\n".format(logger,cliplevel))

    # ES-T attached to Q330s tend to be set to 4g, except in Oregon
    elif "Q330" in logger:
        if "ES" in sensor or "EPISENSOR" in sensor:
            cliplevel = gain * 4 * 9.8
            # these formerly TA now UO Episensors have clip levels set to 2g
            if sensor_sn in ["3818", "3823", "3824", "3825", "3826", "3829", \
                             "3831", "3832", "3833", "3834", "3838", "3841", \
                             "4588", "4590", "7272"]: 
                cliplevel = 0.5 * cliplevel
        elif "STS2" in sensor or "STS-2" in sensor:
            # 1.25 cm/s
            cliplevel = gain * 0.0125 
        elif "G3T" in sensor or "CMG-3T" in sensor:
            # 0.67 cm/s
            cliplevel = gain * 0.0067
        elif "TR240" in sensor or "TRILLIUM 240" in sensor:
            # 1.66 cm/s
            cliplevel = gain * 0.0166
        elif "TR120" in sensor or "TRILLIUM 120" in sensor or "T120PH" in sensor or "T120PA" in sensor:
            # 1.66 cm/s
            cliplevel = gain * 0.0166
        elif "TRCOM" in sensor or "TRILLIUM COMPACT PH" in sensor:
            # 2.6 cm/s
            cliplevel = gain * 0.0260
        logging.debug("Q330 logger: {}, cliplevel: {}\n".format(logger,cliplevel))

    # ES-T and RT147 attached to RT130 dataloggers are set to 4g.
    elif "130" in logger:
        if "ES" in sensor or "147" in sensor:
            cliplevel = gain * 4 * 9.8
        elif "L22" in sensor:
            cliplevel = gain * 0.0001 
        elif "TRCOM" in sensor or "TRILLIUM COMPACT" in sensor:
            # 2.6 cm/s
            cliplevel = gain * 0.026
        elif "TR120" in sensor or "TRILLIUM 120"  in sensor or "TRIL" in sensor:
            # 1.66 cm/s
            cliplevel = gain * 0.0166
        elif "G3ESP" in sensor or "CMG-3ESP" in sensor:
            # 0.5 cm/s
            cliplevel = gain * 0.0050
        elif "GT3134" in sensor or "CMG-3T" in sensor:
            # 0.67 cm/s
            cliplevel = gain * 0.0067
        logging.debug("RT130 logger: {}, cliplevel: {}\n".format(logger,cliplevel))
    elif "SMART" in logger:
        if "HS1" in sensor:
            # small clip
            cliplevel = gain * 0.0001
        logging.debug("SMART logger: {}, cliplevel: {}\n".format(logger,cliplevel))

    return cliplevel

def parse_instrument_identifier(description):
    """
        This method parses the Instrument Identifier (equipment) string and returns 4 strings.
            sensor: PNSN calsta2 shorthand
            sensor_sn: serial number
            logger: PNSN calsta2 shorthand
            logger_sn: serial number
        our equipment strings look like sensor-serial=digitizer-serial
        or sensor-serial=vco=disc=digitizer-serial, i.e. split on '=' and 
        '-' characters. One exception: episensors are 'ES-T' thus include 
        a '-' character.
    """
    if not description:
        raise ValueError("function needs a description string")
    if description.strip() == 'Mark L-4 1 Hz':
        # generic,old, combined displacement response, do not create equipment, only subresponses
        sensor = "OLD_SHORT_PERIOD"
        sensor_sn = "XXXX"
        logger = "LEGACY_ANALOG_DIGITIZER"
        logger_sn = "XXXX"
        return sensor, sensor_sn, logger, logger_sn

    equiplist = description.split('=')
    if len(equiplist) == 2:
        # Two pieces of equipment, assume sensor and digitizer
        dummylist = equiplist[0].split('-')
        if len(dummylist) == 2:
            sensor = dummylist[0]
            sensor_sn = dummylist[1]
        else:
            # episensor is ES-T, i.e. equipment string has extra '-'
            sensor = dummylist[0] + '_' + dummylist[1]
            sensor_sn = dummylist[2]
        logger, logger_sn = equiplist[1].split('-')
    elif len(equiplist) == 4:
        # Four pieces of equipment, assume analog station, sensor,vco,disc,digitizer
        dummylist = equiplist[0].split('-')
        if len(dummylist) == 2:
            sensor = dummylist[0]
            sensor_sn = dummylist[1]
        else:
            # episensor is ES-T, i.e. equipment string has extra '-'
            sensor = dummylist[0] + '_' + dummylist[1]
            sensor_sn = dummylist[2]
        logger, logger_sn = equiplist[3].split('-')
    elif len(equiplist) == 1:
        dummylist = equiplist[0].split(",")
        if len(dummylist) == 3:
            #likely to be a SIS FDSN StationXML --> dataless --> IRIS FDSN StationXML conversion
            sensor = dummylist[0]
            sensor_sn = "XXXX"
            logger = None
            logger_sn = None
    else:
        # Don't know what to do with this
        raise ValueError("don't know how to parse this: "%description)
    return sensor, sensor_sn, logger, logger_sn

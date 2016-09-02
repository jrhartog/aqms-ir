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
                logging.info("candidate conjugate poles: {} and {}, ws={}, fs={}, b={} (compare to {}-{})".format(p1,p2,omega_s,omega_s/(2*np.pi),-1*p1.real/omega_s,f_hp,f_lp))
                break

    if len(fs_candidate) == 0:
        # don't know how to do natural freq and damping w/o conj. pole pairs
        return 0., 0.

    # pick the candidate that is close to a corner frequency
    # for velocity/displacement pick the one close to f_hp, acceleration close to f_lp
    if sensor_type == "VEL":
        df = np.abs(fs_candidate - f_hp) 
    else:
        df = np.abs(fs_candidate - f_lp)
    i_min = np.argmin(df)
    fn = fs_candidate[i_min]
    damp = b_candidate[i_min]
    return fn, damp

def simple_response(sample_rate,response):
    """ 
        Given the obspy ResponseStages, calculate the simple response.
        i.e. the natural frequency, damping factor, low corner, high corner, and overall gain
    """
    EPSILON = 1e-03 # tolerance for normalized amplitude of a pole-zero stage being off from 1.0
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
    f_hp, f_lp = compute_corners(amplitude,frequency)

    # velocity transducer or acceleration?
    if signal_input_units == "M/S" or signal_input_units == "M":
        sensor_type = "VEL"
    else:
        sensor_type = "ACC"

    # try to determine natural frequency and damping factor from poles and corners
    natural_frequency, damping = natural_frequency_and_damping(poles, f_hp, f_lp, sensor_type=sensor_type)
    
    # some sanity checks, limit f_lp to 40% of Nyquist, f_hp must be <= f_lp
    if f_lp > 0.4*sample_rate:
        f_lp = 0.4*sample_rate
    if f_hp > f_lp:
        f_hp = f_lp

    return natural_frequency, damping, f_hp, f_lp, total_gain

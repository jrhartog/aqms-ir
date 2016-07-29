def test_simple_response():
    import matplotlib.pyplot as plt
    try:
        from obspy.signal.invsim import paz_to_freq_resp
    except:
        from obspy.signal.invsim import pazToFreqResp as paz_to_freq_resp
    try:
        from obspy.signal.invsim import paz_2_amplitude_value_of_freq_resp
    except:
        from obspy.signal.invsim import paz2AmpValueOfFreqResp as paz_2_amplitude_value_of_freq_resp

    N = 1024
    sample_rate = 100.
    normalization_frequency = 1.0
    normalization_factor = 1.6
    poles = [(-5.026548 + 3.769911j), (-5.026548 - 3.769911j)]
    zeros = [ complex(0.), complex(0.)]
    amplitude, frequency = paz_to_freq_resp(poles,zeros,normalization_factor,1.0/sample_rate,2*N,freq=True)
    print len(amplitude)
    plt.loglog(frequency,abs(amplitude),basex=10,basey=10)
    plt.show()
    paz = { "poles" : poles, "zeros" : zeros, "gain" : normalization_factor }
    calculated_A0 = paz_2_amplitude_value_of_freq_resp(paz, normalization_frequency)
    if abs(calculated_A0 - 1.0) > 1e-06:
        print "Discrepancy, calculated normalized amplitude: {}, \
               normalization factor {} at normalization frequency {}\
               does not normalize the frequency spectrum.".\
               format(calculated_A0, normalization_factor, normalization_frequency)

if __name__ == "__main__":
    test_simple_response()

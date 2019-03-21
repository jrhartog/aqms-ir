""" inventory is an obspy Inventory object """
import six

import logging
from collections import OrderedDict
import datetime

from .schema import Abbreviation, Format, Unit, Channel, Station, SimpleResponse, AmpParms, CodaParms, Sensitivity

# station or channel end-date when none has been provided
DEFAULT_ENDDATE = datetime.datetime(3000,1,1)

# noise level in m/s used for determining cutoff level for Md
CUTOFF_GM = 1.7297e-7

# units for seismic channels
SEISMIC_UNITS = ['M/S', 'm/s', 'M/S**2', 'm/s**2', 'M/S/S', 'm/s/s', 'CM/S', 'cm/s', 'CM/S**2', 'cm/s**2', 'CM/S/S', 'cm/s/s', 'M', 'm', 'CM', 'cm']

# keep track of successful and failed commits
commit_metrics = OrderedDict()
commit_metrics["stations_good"] = []
commit_metrics["stations_bad"]  = []
commit_metrics["channels_good"] = []
commit_metrics["channels_bad"]  = []
commit_metrics["response_good"] = []
commit_metrics["response_bad"]  = []
commit_metrics["codaparms_good"]= []
commit_metrics["codaparms_bad"] = []
commit_metrics["ampparms_good"] = []
commit_metrics["ampparms_bad"]  = []
commit_metrics["clip_bad"]      = []
commit_metrics["sensitivity_good"] = []
commit_metrics["sensitivity_bad"]  = []

def inventory2db(session, inventory):
    if inventory.networks:
        _networks2db(session, inventory.networks)
    else:
        logging.warning("This inventory has no networks, doing nothing.")
    return

def _networks2db(session, networks):
    for network in networks:
        _network2db(session,network)
    return

def _network2db(session, network):
    net_id = None
    if network.stations:
        success,failed = _stations2db(session,network)
        logging.info("\n Success: {} stations, failure: {} stations.\n".format(success,failed))
    else:
        # only insert an entry into D_Abbreviation
        net_id = _get_net_id(session, network)
        if not net_id:
            logging.warning("Did not add network description to database")
    return

def _get_net_id(session, network):
    """ 
       given obspy Network object 
       get id from d_abbreviation with
       same description (creates a new entry
       if none exists yet).
    """
    result = session.query(Abbreviation).filter_by(description=network.description).first()
    if result:
        return result.id
    else:
        network_entry = Abbreviation(description=network.description)
        session.add(network_entry)
        try:
            session.commit()
            result = session.query(Abbreviation).filter_by(description=network.description).first()
            return result.id
        except:
            logging.error("Not able to commit abbreviation and get net_id")
    return None

def _get_inid(session, channel):
    """ 
       get id from d_abbreviation with
       same instrument type description (creates a new entry
       if none exists yet).
    """
    result = session.query(Abbreviation).filter_by(description=channel.sensor.description).first()
    if result:
        return result.id
    else:
        instr_entry = Abbreviation(description=channel.sensor.description)
        session.add(instr_entry)
        try:
            session.commit()
            result = session.query(Abbreviation).filter_by(description=channel.sensor.description).first()
            return result.id
        except:
            logging.error("Not able to commit abbreviation and get inid")
    return None

def _get_unit(session, unit_name, unit_description):
    """ 
       get id from d_unit with
       same unit description (creates a new entry
       if none exists yet).
    """
    result = session.query(Unit).filter_by(name=unit_name, description=unit_description).first()
    if result:
        return result.id
    else:
        instr_entry = Unit(name=unit_name, description=unit_description)
        session.add(instr_entry)
        try:
            session.commit()
            result = session.query(Unit).filter_by(name=unit_name, description=unit_description).first()
            return result.id
        except:
            logging.error("Not able to commit abbreviation and get unit id")
    return None

def _get_format_id(session, format_name=None):
    """ 
       get id from d_format
       (creates a new entry
       if none exists yet).
    """
    if not format_name:
        format_name="UNKNOWN"

    result = session.query(Format).filter_by(name=format_name).first()

    if result:
        return result.id
    else:
        instr_entry = Format(name=format_name)
        session.add(instr_entry)
        try:
            session.commit()
            result = session.query(Format).filter_by(name=format_name).first()
            return result.id
        except:
            logging.error("Not able to commit format_name and get format id")
    return None

def _remove_station(session, network, station):
    """
        Removes this station from station_data and will remove
        its channels as well. See remove_channels.
    """
    network_code = network.code
    station_code = station.code

    status = 0

    try:
        status = session.query(Station).filter_by(net=network_code,sta=station_code).delete()
    except Exception as e:
        logging.error("remove_station: {}".format(e))

    try:
        session.commit()
    except Exception as e:
        logging.error("Unable to delete station {}.{}: {}".format(network_code,station_code,e))
        sys.exit()

    if station.channels:
        status = status + _remove_channels(session, network_code, station)
    
    return status

def _remove_channels(session, network_code, station):
    station_code = station.code
    status = 0
    # remove all channels for this station, not just the ones in the XML file
    try:
        status = session.query(Channel).filter_by(net=network_code,sta=station_code).delete()
    except Exception as e:
        logging.error("Unable to delete channels: {}.{}: {}".format(network_code,station_code,e))

    try:
        status = _remove_simple_responses(session, network_code, station_code)
    except Exception as e:
        logging.error("Unable to delete responses: {}.{}: {}".format(network_code,station_code,e))

    try:
        status = _remove_sensitivity(session, network_code, station_code)
    except Exception as e:
        logging.error("Unable to delete overall sensitivity: {}.{}: {}".format(network_code,station_code,e))

    #for channel in station.channels:
    #    try:
    #        status = status + _remove_channel(session, network_code, station_code, channel)
    #    except Exception as e:
    #        logging.error("Unable to delete channel {}.{}.{}.{}: {}".format( \
    #        network_code, station_code, channel.code, channel.location_code, e))
    #        continue # next channel
    return status

def _remove_simple_responses(session, network_code, station_code):

    try:
        status = session.query(SimpleResponse).filter_by(net=network_code,sta=station_code).delete()
    except Exception as e:
        logging.error("remove_simple_responses: {}.{}: {}".format(network_code,station_code,e))

    try:
        status = session.query(CodaParms).filter_by(net=network_code,sta=station_code).delete()
    except Exception as er:
        logging.error("remove_simple_responses, codaparms: {}.{}: {}".format(network_code,station_code,er))

    try:
        status = session.query(AmpParms).filter_by(net=network_code,sta=station_code).delete()
    except Exception as error:
        logging.error("remove_simple_responses,ampparms: {}.{}: {}".format(network_code,station_code,error))

    return status

def _remove_sensitivity(session, network_code, station_code):

    try:
        status = session.query(Sensitivity).filter_by(net=network_code,sta=station_code).delete()
    except Exception as e:
        logging.error("remove_sensitivity: {}.{}: {}".format(network_code,station_code,e))

    return status

def _remove_channel(session, network_code, station_code, channel):
    """
        Removes this station from station_data and will remove
        its channels as well. See remove_channels.
    """
    status = 0
    try:
        status = session.query(Channel).filter_by(net=network_code,sta=station_code \
                 ,seedchan=channel.code,location=fix(channel.location_code)).delete()
    except Exception as e:
        logging.error("remove_channel: {}".format(e))

    try:
        session.commit()
    except Exception as e:
        logging.error("Unable to delete channel {}.{}.{}.{}: {}".format(network_code,station_code,channel.code, channel.location_code,e))

    if channel.response:
        try:
            my_status = _remove_simple_response(session, network_code, station_code, channel.code, channel.location_code)
        except Exception as e:
            logging.error("remove_channel ({}): {}".format(my_status, e))

    return status

def _remove_simple_response(session, network_code, station_code, channel_code, location_code):

    try:
        status = session.query(SimpleResponse).filter_by(net=network_code,sta=station_code \
                     ,seedchan=channel_code,location=fix(location_code)).delete()
    except Exception as e:
        logging.error("remove_simple_response: {}".format(e))

    try:
        status = session.query(CodaParms).filter_by(net=network_code,sta=station_code \
                 ,seedchan=channel_code,location=fix(location_code)).delete()
    except Exception as er:
        logging.error("remove_simple_response, codaparms: {}".format(er))

    try:
        status = session.query(AmpParms).filter_by(net=network_code,sta=station_code \
                 ,seedchan=channel_code,location=fix(location_code)).delete()
    except Exception as error:
        logging.error("remove_simple_response,ampparms: {}".format(error))

    return status

def _station2db(session, network, station):

    net_id = _get_net_id(session,network)
    network_code = network.code
    station_code = station.code
    default_enddate = datetime.datetime(3000,1,1)
    # first remove any prior meta-data associated with Net-Sta and Net-Sta-Chan-Loc
    try:
        status = _remove_station(session,network,station)
        logging.info("Removed {} channels for station {}".format(status-1,station_code))
    except Exception as e:
        logging.error("Exception: {}".format(e))

    db_station = Station(net=network.code, sta=station.code, ondate=station.start_date.datetime)
    session.add(db_station)

    db_station.net_id = net_id
    if hasattr(station,"end_date") and station.end_date:
        db_station.offdate = station.end_date.datetime
    else:
        db_station.offdate = DEFAULT_ENDDATE
    db_station.lat = station.latitude
    db_station.lon = station.longitude
    db_station.elev = station.elevation
    db_station.staname = station.site.name

    try:
        session.commit()
        commit_metrics["stations_good"].append(station_code)
    except Exception as e:
        logging.error("Cannot save station_data: {}".format(e))
        commit_metrics["stations_bad"].append(station_code)
        

    if station.channels:
        _channels2db(session, network_code, station_code, station.channels)
    return

def _stations2db(session, network):
    success = 0
    failed = 0
    for station in network.stations:
        try:
             _station2db(session, network, station)
             success = success + 1
        except Exception as e:
            logging.error("Unable to add station {} to db: {}".format(station.code, e))
            failed = failed + 1
            continue
    return success, failed

def _channel2db(session, network_code, station_code, channel):

    inid = _get_inid(session, channel)
    calib_unit = _get_unit(session, channel.calibration_units, channel.calibration_units_description)
    if hasattr(channel.response,"instrument_sensitivity") and channel.response.instrument_sensitivity:
        signal_unit = _get_unit(session, channel.response.instrument_sensitivity.input_units, channel.response.instrument_sensitivity.input_units_description)
    elif hasattr(channel.response,"instrument_polynomial"):
        signal_unit = _get_unit(session, channel.response.instrument_polynomial.input_units, channel.response.instrument_polynomial.input_units_description)
    else:
        signal_unit=None

    format_id = _get_format_id(session)

    db_channel = Channel(net=network_code, sta=station_code, seedchan=channel.code, location=fix(channel.location_code), ondate=channel.start_date.datetime)
    session.add(db_channel)

    if inid:
        db_channel.inid = inid

    if signal_unit:
        db_channel.unit_signal = signal_unit
    if calib_unit:
        db_channel.unit_calib = calib_unit
    db_channel.format_id = format_id
    if hasattr(channel,"end_date") and channel.end_date:
        db_channel.offdate = channel.end_date.datetime
    else:
        db_channel.offdate = DEFAULT_ENDDATE
    db_channel.lat = channel.latitude
    db_channel.lon = channel.longitude
    db_channel.elev = channel.elevation
    db_channel.edepth = channel.depth
    db_channel.azimuth = float(channel.azimuth)
    db_channel.dip = float(channel.dip)
    db_channel.samprate = float(channel.sample_rate)
    db_channel.flags = ''.join(t[0] for t in channel.types)

    try:
        session.commit()
        commit_metrics["channels_good"].append(station_code + "." + channel.code)
    except Exception as e:
        logging.error("Cannot save to channel_data: {}".format(e))
        commit_metrics["channels_bad"].append(station_code + "." + channel.code)

    if channel.response:
        try:
            _response2db(session, network_code, station_code, channel)
        except Exception as e:
            logging.error("Unable to add response for {}.{}.{} to db: {}".format(network_code,station_code,channel.code,e))

    return


def _channels2db(session, network_code, station_code, channels):
    for channel in channels:
        try:
            _channel2db(session, network_code, station_code, channel)
        except Exception as e:
            logging.error("Unable to add channel {} to db: {}".format(channel.code, e))
            continue
    return

def _response2db(session, network_code, station_code, channel,fill_all=False):

    # for now, only fill simple_response, channelmap_ampparms and channelmap_codaparms tables
    _simple_response2db(session,network_code,station_code,channel)

    # overall sensitivity
    if hasattr(channel.response,"instrument_sensitivity") and channel.response.instrument_sensitivity:
        _sensitivity2db(session,network_code,station_code,channel)

    if fill_all:
        # do all IR tables, not implemented yet.
        pass

    return

def _simple_response2db(session,network_code,station_code,channel):
    from .util import simple_response, parse_instrument_identifier, get_cliplevel

    if not hasattr(channel.response,"instrument_sensitivity") or not channel.response.instrument_sensitivity:
        logging.warning("{}-{} does not have an instrument sensitivity, no response".format(station_code,channel.code))
        return

    if not hasattr(channel.response.instrument_sensitivity,"input_units") or \
           channel.response.instrument_sensitivity.input_units not in SEISMIC_UNITS:
        logging.warning("{}-{} is not a seismic component, no response".format(station_code,channel.code))
        return

    fn, damping, lowest_freq, highest_freq, gain = simple_response(channel.sample_rate,channel.response)

    db_simple_response = SimpleResponse(net=network_code, sta=station_code, \
                         seedchan=channel.code, location=fix(channel.location_code), \
                         ondate=channel.start_date.datetime)

    session.add(db_simple_response)

    db_simple_response.channel = channel.code
    db_simple_response.natural_frequency = fn
    db_simple_response.damping_constant = damping
    db_simple_response.gain = gain
    db_simple_response.gain_units = "DU/" + channel.response.instrument_sensitivity.input_units
    db_simple_response.low_freq_corner = highest_freq
    db_simple_response.high_freq_corner = lowest_freq
    if hasattr(channel,"end_date") and channel.end_date:
        db_simple_response.offdate = channel.end_date.datetime
    else:
        db_simple_response.offdate = DEFAULT_ENDDATE

    try:
        session.commit()
        commit_metrics["response_good"].append(station_code + "." + channel.code)
    except Exception as e:
        logging.error("Unable to add simple_response {} to db: {}".format(db_simple_response,e))
        commit_metrics["response_bad"].append(station_code + "." + channel.code)

    # next fill channelmap_codaparms (only for seismic channels, verticals)
    if channel.dip != 0.0:

        db_codaparms = CodaParms(net=network_code, sta=station_code, \
                       seedchan=channel.code, location=fix(channel.location_code), \
                       ondate=channel.start_date.datetime)
        session.add(db_codaparms)
        db_codaparms.channel = channel.code
        db_codaparms.cutoff = gain * CUTOFF_GM # cutoff in counts
        # this is too low for strong-motion channels, multiply with 1000 to get something reasonable
        if channel.code[1] == "N":
            db_codaparms.cutoff = 1000.0 * db_codaparms.cutoff
        if hasattr(channel,"end_date") and channel.end_date:
            db_codaparms.offdate = channel.end_date.datetime
        else:
            db_codaparms.offdate = DEFAULT_ENDDATE
        try:
            session.commit()
            commit_metrics["codaparms_good"].append(station_code + "." + channel.code)
        except Exception as er:
            logging.error("Unable to add codaparms {} to db: {}".format(db_codaparms,er))
            commit_metrics["codaparms_bad"].append(station_code + "." + channel.code)

    # next fill channelmap_ampparms, for seismic channels only, all components

    if network_code in ["UW", "CC", "UO", "HW"]:

        # get sensor and logger info
        if "=" in channel.sensor.description and "-" in channel.sensor.description:
            # PNSN instrument identifier
            sensor, sensor_sn, logger, logger_sn = parse_instrument_identifier(channel.sensor.description)
        elif len(channel.sensor.description.split(",")) == 3:
            # possibly instrument identifier from SIS dataless->IRIS->StationXML
            sensor, sensor_sn, logger, logger_sn = parse_instrument_identifier(channel.sensor.description)
        else:
            sensor = channel.sensor.type
            sensor_sn = channel.sensor.serial_number
            logger = channel.data_logger.type
            logger_sn = channel.data_logger.serial_number

        logging.info("{}-{}: channel equipment: {}-{}={}-{}".format(station_code,channel.code,sensor,sensor_sn,logger,logger_sn))

        try:
            clip = get_cliplevel(sensor,sensor_sn,logger,logger_sn, gain)
        except Exception as err:
            logging.error("Cannot determine cliplevel {}: {}".format(channel.sensor,err))

    else:
        # first see if there is something like 2g,3g,4g in instrument identifier
        if "2g" in channel.sensor.description:
            clip = gain * 2 * 9.8
        elif "4g" in channel.sensor.description:
            clip = gain * 4 * 9.8
        elif "1g" in channel.sensor.description:
            clip = gain * 9.8
        elif "3g" in channel.sensor.description:
            clip = gain * 3 * 9.8
        elif channel.code[1] == "N" or channel.code[1] == "L":
            # strong-motion, assume 4g
            clip = gain * 4 * 9.8
        elif channel.code[0:2] in ["EH", "SH"]:
            # short-period
            clip = gain * 0.0001
        elif channel.code[0:2] in ["LH", "MH", "BH", "HH"]:
            # 1 cm/s
            clip = gain * 0.0100
        else:
            clip = -1
        
    # have clip, fill channelmap_ampparms                
    db_ampparms = AmpParms(net=network_code, sta=station_code, \
                  seedchan=channel.code, location=fix(channel.location_code), \
                  ondate=channel.start_date.datetime)

    session.add(db_ampparms)
    db_ampparms.channel = channel.code
    db_ampparms.clip = clip
    if hasattr(channel,"end_date") and channel.end_date:
        db_ampparms.offdate = channel.end_date.datetime
    else:
        db_ampparms.offdate = DEFAULT_ENDDATE
    if not clip or clip == -1:
        commit_metrics["clip_bad"].append(station_code + "." + channel.code)
    try:
        session.commit()
        commit_metrics["ampparms_good"].append(station_code + "." + channel.code)
    except Exception as error:
        logging.error("Unable to add ampparms {} to db: {}".format(db_ampparms,error))
        commit_metrics["ampparms_bad"].append(station_code + "." + channel.code)

    return

def _sensitivity2db(session,network_code,station_code,channel):
    db_sensitivity = Sensitivity(net=network_code, sta=station_code, seedchan=channel.code, location=fix(channel.location_code), ondate=channel.start_date.datetime)
    session.add(db_sensitivity)
    db_sensitivity.stage_seq = 0
    db_sensitivity.sensitivity = channel.response.instrument_sensitivity.value
    db_sensitivity.frequency = channel.response.instrument_sensitivity.frequency
    if hasattr(channel,"end_date") and channel.end_date:
        db_sensitivity.offdate = channel.end_date.datetime
    else:
        db_sensitivity.offdate = DEFAULT_ENDDATE

    try:
        session.commit()
        commit_metrics["sensitivity_good"].append(station_code + "." + channel.code)
    except Exception as error:
        logging.error("Unable to add overall sensitivity {} to db: {}".format(db_sensitivity,error))
        commit_metrics["sensitivity_bad"].append(station_code + "." + channel.code)

    return
    

def fix(location):
    if location == "":
        return "  "
    else:
        return location

def print_metrics(bad_only=True, abbreviated=False):
    for k,v in six.iteritems(commit_metrics):
        if len(v) > 0:
            if bad_only and "bad" in k:
                if abbreviated:
                    print("{}: {}".format(k,len(v)))
                else:
                    print_metric(k,v)
            elif not bad_only:
                if abbreviated:
                    print("{}: {}".format(k,len(v)))
                else:
                    print_metric(k,v)
    return

def print_metric(key, values):

    indent = "    "
    print("{}\n:".format(key))
    for v in values:
        print("{}{}".format(indent,v))
    return
    
     
    

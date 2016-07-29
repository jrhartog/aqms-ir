""" inventory is an obspy Inventory object """
import logging

from schema import Abbreviation, Format, Unit, Channel, Station

def inventory2db(session, inventory):
    if inventory.networks:
        networks2db(session, inventory.networks)
    else:
        logging.warning("This inventory has no networks, doing nothing.")
    return

def networks2db(session, networks):
    for network in networks:
        network2db(session,network)
    return

def network2db(session, network):
    net_id = None
    if network.stations:
        stations2db(session,network)
    else:
        # only insert an entry into D_Abbreviation
        net_id = get_net_id(session, network)
        if not net_id:
            logging.warning("Did not add network description to database")
    return

def get_net_id(session, network):
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
        print network_entry.id
        try:
            session.commit()
            result = session.query(Abbreviation).filter_by(description=network.description).first()
            return result.id
        except:
            logging.error("Not able to commit abbreviation and get net_id")
    return None

def get_inid(session, channel):
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
        print instr_entry.id
        try:
            session.commit()
            result = session.query(Abbreviation).filter_by(description=channel.sensor.description).first()
            return result.id
        except:
            logging.error("Not able to commit abbreviation and get inid")
    return None

def get_unit(session, unit_name, unit_description):
    """ 
       get id from d_abbreviation with
       same instrument type description (creates a new entry
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

def get_format_id(session, format_name=None):
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

def remove_station(session, network, station):
    """
        Removes this station from station_data and will remove
        its channels as well. See remove_channels.
    """
    network_code = network.code
    station_code = station.code

    try:
        status = session.query(Station).filter(net=network_code,sta=station_code).delete()
    except Exception as e:
        logging.error("remove_station: {}".format(e))

    try:
        session.commit()
    except Exception as e:
        logging.error("Unable to delete station {}.{}: {}".format(network_code,station_code,e))
        sys.exit()

    if station.channels:
        status = status + remove_channels(session, network_code, station)
    
    return status

def station2db(session, network, station):

    net_id = get_net_id(session,network)
    network_code = network.code
    station_code = station.code
    # first remove any prior meta-data associated with Net-Sta and Net-Sta-Chan-Loc
    try:
        status = remove_station(network,station)
    except Exception as e:
        logging.error("Exception: {}".format(e))

    try:
        db_station = session.query(Station).filter_by(net=network.code, sta=station.code).one()
    except Exception as e:
        logging.error("Exception: {}".format(e))
        db_station = Station(net=network.code, sta=station.code, ondate=station.start_date.datetime)
        session.add(db_station)

    db_station.net_id = net_id
    db_station.offdate = station.end_date.datetime
    db_station.lat = station.latitude
    db_station.lon = station.longitude
    db_station.elev = station.elevation
    db_station.staname = station.site.name

    try:
        session.commit()
    except Exception as e:
        logging.error("Cannot save station_data: {}".format(e))
        

    if station.channels:
        channels2db(session, network_code, station_code, station.channels)
    return

def stations2db(session, network):
    for station in network.stations:
        try:
             station2db(session, network, station)
        except Exception as e:
            print "Unable to add station {} to db: {}".format(station.code, e)
            continue
    return

def channel2db(session, network_code, station_code, channel):

    inid = get_inid(session, channel)
    calib_unit = get_unit(session, channel.calibration_units, channel.calibration_units_description)
    signal_unit = get_unit(session, channel.response.instrument_sensitivity.input_units, channel.response.instrument_sensitivity.input_units_description)
    format_id = get_format_id(session)

    #try:
        #db_channel = session.query(Channel).filter_by(net=network_code, \
        #             sta=station_code, seedchan=channel.code, \
        #             location=channel.location_code, \
        #             ondate=channel.start_date.datetime).one()
    #except Exception as e:
        #logging.info("Channel not in db: {}".format(e))
        # check to see if there are other epochs for this channel, if so, delete them. Too difficult to figure out what user wants to do (insert, replace, etc.)
        # removed = session.query(Channel).filter(net=network_code, sta=station_code, seedchan=channel.code, location=channel.location_code, ondate != channel.start_data.datetime).delete()
        # if removed > 0:
        #     logging.info("Removed {} epochs for channel {}.{}.{}.{}\n".format(removed,network_code, station_code, channel.code, channel.location_code))
        # create the new entry
    db_channel = Channel(net=network_code, sta=station_code, seedchan=channel.code, location=channel.location_code, ondate=channel.start_date.datetime)
    session.add(db_channel)
            

    if inid:
        db_channel.inid = inid

    db_channel.unit_signal = signal_unit
    db_channel.unit_calib = calib_unit
    db_channel.format_id = format_id
    db_channel.offdate = channel.end_date.datetime
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
    except Exception as e:
        logging.error("Cannot save to channel_data: {}".format(e))

    if channel.response:
        try:
            response2db(session, network_code, station_code, channel) \
        except Exception as e:
            print "Unable to add response for {}.{}.{} to db: {}".format(network_code,station_code,channel.code,e)
            continue
    return


def channels2db(session, network_code, station_code, channels):
    for channel in channels:
        try:
            channel2db(session, network_code, station_code, channel)
        except Exception as e:
            print "Unable to add channel {} to db: {}".format(channel.code, e)
            continue
    return

def response2db(session, network_code, station_code, channel,fill_all=False):

    # for now, only fill simple_response table
    simple_response2db(session,network_code,station_code,channel)

    if fill_all:
        # do all IR tables, not implemented yet.
        pass

    return

def simple_response2db(session,network_code,station_code,channel):
    from util import simple_response

    fn, damping, lowest_freq, highest_freq, gain = simple_response(channel.response)
    db_simple_response = SimpleResponse(net=network_code, sta=station_code, \
                         seedchan=channel.code, location=channel.location_code, \
                         ondate=channel.start_date.datetime)

    session.add(db_simple_response)

    db_simple_response.channel = channel.code
    db_simple_response.natural_frequency = fn
    db_simple_response.damping_constant = damping
    db_simple_response.gain = gain
    db_simple_response.gain_units = "DU/" + channel.input_units
    db_simple_response.low_freq_corner = highest_freq
    db_simple_response.high_freq_corner = lowest_freq
    db_simple_response.offdate = channel.end_date.datetime

    try:
        session.commit()
    except Exception as e:
        print "Unable to add simple_response {} to db".format(db_simple_response,e)
        continue
    return

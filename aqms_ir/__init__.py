"""
    aqms_ir: methods to translate from obspy.Inventory to AQMS Instrument Response database schema
    v. 0.0.1: only fills tables station_data, channel_data, and simple_response, and associated dictionary tables.
    for a full description of the AQMS Instrument Response schema, see http://www.ncedc.org/db
    Note: this, so far, has only been tested on a PostgreSQL database with the tables Station_Data, Channel_Data, and Instrument Response
    Use at your own risk!
    
    Copyright 2017 Renate Hartog
"""

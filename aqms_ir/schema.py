"""
    Classes that describe tables
"""
import datetime

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import text
from sqlalchemy import Column, DateTime, Integer, Numeric, String, ForeignKey
from sqlalchemy import Sequence

# create the base class of all ORM classes
Base = declarative_base()

class Abbreviation(Base):
    __tablename__ = "d_abbreviation"

    id = Column('id', Integer, Sequence('abbseq'), primary_key=True, nullable=False)
    description = Column('description', String)

    def __repr__(self):
        return "Abbreviation: id={}, description={}".\
        format(self.id, self.description)

class Unit(Base):
    __tablename__ = "d_unit"

    id = Column('id', Integer, Sequence('uniseq'), primary_key=True, nullable=False)
    name = Column('name', String(80))
    description = Column('description', String(70))
    
    def __repr__(self):
        return "Unit: id={}, name={}, description={}".format(\
        self.id, self.name, self.description)

class Format(Base):
    __tablename__ = "d_format"

    id = Column('id', Integer, Sequence('forseq'), primary_key=True, nullable=False)
    name = Column('name', String(80), default="UNKNOWN")
    family = Column('family', Integer, nullable=False, default=50)
    ms_id = Column('ms_id', Integer, nullable=False, default=0)
    
    def __repr__(self):
        return "Format: id={}, name={}, family={}, ms_id={}".format(\
        self.id, self.name, self.family, self.ms_id)

class Station(Base):
    __tablename__ = "station_data"

    net = Column('net', String, primary_key=True, nullable=False)
    sta = Column('sta', String, primary_key=True, nullable=False)
    ondate = Column('ondate', DateTime, primary_key=True, nullable=False)
    lat = Column('lat', Numeric)
    lon = Column('lon', Numeric)
    elev = Column('elev', Numeric)
    staname = Column('staname', String)
    net_id = Column('net_id', ForeignKey('d_abbreviation.id'),
                    info="key to network description in d_abbreviation")
    word_32 = Column('word_32', Numeric, nullable=False, default=3210)
    word_16 = Column('word_16', Numeric, nullable=False, default=10)
    offdate = Column('offdate', DateTime, default=datetime.datetime(3000,1,1))
    lddate = Column('lddate', DateTime, server_default=text('NOW()'))

    def __repr__(self):
        return "Station: net={}, sta={}, ondate={}, staname={}, lat={}, lon={}, elev={}".\
        format(self.net,self.sta,self.ondate.isoformat(),self.staname,self.lat,self.lon,self.elev)

class Channel(Base):
    __tablename__ = "channel_data"

    net = Column('net', String(8), primary_key=True, nullable=False)
    sta = Column('sta', String(6), primary_key=True, nullable=False)
    seedchan = Column('seedchan', String(3), primary_key=True, nullable=False)
    location = Column('location', String(2), primary_key=True, nullable=False)
    ondate = Column('ondate', DateTime, primary_key=True, nullable=False)
    channel = Column('channel', String(8))
    channelsrc = Column('channelsrc', String(8), default="SEED")
    inid = Column('inid', ForeignKey('d_abbreviation.id'), 
                  info="key to instrument description in d_abbreviation")
    remark = Column('remark', String(30))
    unit_signal = Column('unit_signal', ForeignKey('d_unit.id'),
                  info="key to ground motion signal unit description in d_unit")
    unit_calib = Column('unit_calib', ForeignKey('d_unit.id'),
                  info="key to calibration signal unit description in d_unit")
    lat = Column('lat', Numeric)
    lon = Column('lon', Numeric)
    elev = Column('elev', Numeric)
    edepth = Column('edepth', Numeric)
    azimuth = Column('azimuth', Numeric)
    dip = Column('dip', Numeric)
    format_id = Column('format_id', ForeignKey('d_format.id'),
                       info="key to data format description in d_format", nullable=False)
    record_length = Column('record_length', Integer)
    samprate = Column('samprate', Numeric, nullable=False)
    clock_drift = Column('clock_drift', Numeric)
    flags = Column('flags', String(27), info="channel flags", default="CG")
    offdate = Column('offdate', DateTime, default=datetime.datetime(3000,1,1))
    lddate = Column('lddate', DateTime, server_default=text('NOW()'))

    def __repr__(self):
        return "Channel: net={}, sta={}, seedchan={}, location={}, ondate={}, offdate={}".\
        format(self.net, self.sta, self.seedchan, self.location, self.ondate, self.offdate)

class SimpleResponse(Base):
    __tablename__ = "simple_response"

    net = Column('net', String(8), primary_key=True, nullable=False)
    sta = Column('sta', String(6), primary_key=True, nullable=False)
    seedchan = Column('seedchan', String(3), primary_key=True, nullable=False)
    location = Column('location', String(2), primary_key=True, nullable=False)
    ondate = Column('ondate', DateTime, primary_key=True, nullable=False)
    channel = Column('channel', String(8))
    channelsrc = Column('channelsrc', String(8), default="SEED")
    natural_frequency = Column('natural_frequency', Numeric)
    damping_constant = Column('damping_constant', Numeric)
    gain = Column('gain', Numeric)
    gain_units = Column('gain_units', String)
    low_freq_corner = Column('low_freq_corner', Numeric)
    high_freq_corner = Column('high_freq_corner', Numeric)
    offdate = Column('offdate', DateTime, default=datetime.datetime(3000,1,1))
    lddate = Column('lddate', DateTime, server_default=text('NOW()'))
    dlogsens = Column('dlogsens', Numeric)

    def __repr__(self):
        return "SimpleResponse: net={}, sta={}, seedchan={}, location={}, ondate={}, \
                offdate={}, gain={} ({}), low_freq_cutoff={}, high_freq_cutoff={}, \
                natural_frequency={}, damping_constant={}".\
                format(self.net, self.sta, self.seedchan, self.location, self.ondate, \
                self.offdate, self.gain, self.gain_units, self.low_freq_corner, self.high_freq_corner, \
                self.natural_frequency, self.damping_constant)

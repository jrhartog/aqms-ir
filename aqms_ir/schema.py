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

class AmpParms(Base):
    __tablename__ = "channelmap_ampparms"

    net = Column('net', String(8), primary_key=True, nullable=False)
    sta = Column('sta', String(6), primary_key=True, nullable=False)
    seedchan = Column('seedchan', String(3), primary_key=True, nullable=False)
    location = Column('location', String(2), primary_key=True, nullable=False)
    ondate = Column('ondate', DateTime, primary_key=True, nullable=False)
    offdate = Column('offdate', DateTime, default=datetime.datetime(3000,1,1))
    channel = Column('channel', String(8))
    channelsrc = Column('channelsrc', String(8), default="SEED")
    clip = Column('clip', Numeric)
    lddate = Column('lddate', DateTime, server_default=text('NOW()'))

    def __repr__(self):
        return "AmpParms: net={}, sta={}, seedchan={}, location={}, ondate={}, \
                offdate={}, clip={}".\
                format(self.net, self.sta, self.seedchan, self.location, self.ondate, \
                self.offdate, self.clip)

class CodaParms(Base):
    __tablename__ = "channelmap_codaparms"

    net = Column('net', String(8), primary_key=True, nullable=False)
    sta = Column('sta', String(6), primary_key=True, nullable=False)
    seedchan = Column('seedchan', String(3), primary_key=True, nullable=False)
    location = Column('location', String(2), primary_key=True, nullable=False)
    ondate = Column('ondate', DateTime, primary_key=True, nullable=False)
    offdate = Column('offdate', DateTime, default=datetime.datetime(3000,1,1))
    channel = Column('channel', String(8))
    channelsrc = Column('channelsrc', String(8), default="SEED")
    cutoff = Column('cutoff', Numeric)
    gain_corr = Column('gain_corr', Numeric)
    summary_wt = Column('summary_wt', Numeric)
    lddate = Column('lddate', DateTime, server_default=text('NOW()'))

    def __repr__(self):
        return "CodaParms: net={}, sta={}, seedchan={}, location={}, ondate={}, \
                offdate={}, cutoff={}, gain_corr={}, summary_wt={}".\
                format(self.net, self.sta, self.seedchan, self.location, self.ondate, \
                self.offdate, self.cutoff, self.gain_corr, self.summary_wt)


class Sensitivity(Base):
    __tablename__ = "sensitivity"

    net = Column('net', String(8), primary_key=True, nullable=False)
    sta = Column('sta', String(6), primary_key=True, nullable=False)
    seedchan = Column('seedchan', String(3), primary_key=True, nullable=False)
    location = Column('location', String(2), primary_key=True, nullable=False)
    ondate = Column('ondate', DateTime, primary_key=True, nullable=False)
    offdate = Column('offdate', DateTime, default=datetime.datetime(3000,1,1))
    stage_seq = Column('stage_seq', Integer)
    channel = Column('channel', String(8))
    channelsrc = Column('channelsrc', String(8), default="SEED")
    sensitivity = Column('sensitivity', Numeric)
    frequency = Column('frequency', Numeric)
    lddate = Column('lddate', DateTime, server_default=text('NOW()'))

    def __repr__(self):
        return "Sensitivity: net={}, sta={}, seedchan={}, location={}, ondate={}, \
                offdate={}, stage_seq={}, sensitivity={}, frequency={}".\
                format(self.net, self.sta, self.seedchan, self.location, self.ondate, \
                self.offdate, self.stage_seq, self.sensitivity, self.frequency)


"""
archdb1=> \d poles_zeros
                                        Table "trinetdb.poles_zeros"
   Column   |            Type             | Collation | Nullable |                 Default
------------+-----------------------------+-----------+----------+------------------------------------------
 net        | character varying(8)        |           | not null |
 sta        | character varying(6)        |           | not null |
 seedchan   | character varying(3)        |           | not null |
 location   | character varying(2)        |           | not null |
 ondate     | timestamp without time zone |           | not null |
 stage_seq  | integer                     |           | not null |
 channel    | character varying(8)        |           |          |
 channelsrc | character varying(8)        |           |          |
 offdate    | timestamp without time zone |           |          |
 pz_key     | integer                     |           | not null |
 tf_type    | character varying(1)        |           |          |
 unit_in    | integer                     |           | not null |
 unit_out   | integer                     |           | not null |
 ao         | double precision            |           | not null |
 af         | double precision            |           |          |
 lddate     | timestamp without time zone |           |          | timezone('UTC'::text, CURRENT_TIMESTAMP)
Indexes:
    "p_z00" PRIMARY KEY, btree (net, sta, seedchan, location, ondate, stage_seq)
"""
class Poles_Zeros(Base):
    __tablename__ = "poles_zeros"

    net = Column('net', String(8), primary_key=True, nullable=False)
    sta = Column('sta', String(6), primary_key=True, nullable=False)
    seedchan = Column('seedchan', String(3), primary_key=True, nullable=False)
    location = Column('location', String(2), primary_key=True, nullable=False)
    ondate = Column('ondate', DateTime, primary_key=True, nullable=False)
    offdate = Column('offdate', DateTime, default=datetime.datetime(3000,1,1))
    channel = Column('channel', String(8))
    channelsrc = Column('channelsrc', String(8), default="SEED")
    #stage_seq = Column('stage_seq', Integer)
    stage_seq = Column('stage_seq', Integer, primary_key=True, nullable=False)
    tf_type  = Column('tf_type', String(1))

    pz_key   = Column('pz_key', ForeignKey('pz.key'),
                      info="key to PZ to get to list of PZ_Data rows", nullable=False)

    unit_in  = Column('unit_in', Integer, nullable=False)
    unit_out = Column('unit_out', Integer, nullable=False)
    ao = Column('ao', Numeric, nullable=False)
    af = Column('af', Numeric)
    lddate = Column('lddate', DateTime, server_default=text('NOW()'))

    def __repr__(self):
        return "Poles_Zeros: net={}, sta={}, seedchan={}, location={}, ondate={}, \
                offdate={}, stage_seq={}, ao={}, af={}, unit_in={}, unit_out={}".\
                format(self.net, self.sta, self.seedchan, self.location, self.ondate, \
                self.offdate, self.stage_seq, self.ao, self.af, self.unit_in, self.unit_out)

"""
archdb1=> \d pz
                                          Table "trinetdb.pz"
 Column |            Type             | Collation | Nullable |                 Default
--------+-----------------------------+-----------+----------+------------------------------------------
 key    | integer                     |           | not null |
 name   | character varying(80)       |           |          |
 lddate | timestamp without time zone |           |          | timezone('UTC'::text, CURRENT_TIMESTAMP)
Indexes:
    "pz00" PRIMARY KEY, btree (key)
"""
class PZ(Base):
    __tablename__ = "pz"

    key  = Column('key', Integer, Sequence('pzseq'), primary_key=True, nullable=False)
    name = Column('name', String(80))
    lddate = Column('lddate', DateTime, server_default=text('NOW()'))

    def __repr__(self):
        return "class PZ: key={}, name=[{}]".format(self.key, self.name)

"""
archdb1=> \d pz_data
                    Table "trinetdb.pz_data"
 Column  |         Type         | Collation | Nullable | Default
---------+----------------------+-----------+----------+---------
 key     | integer              |           | not null |
 row_key | integer              |           | not null |
 type    | character varying(1) |           |          |
 r_value | double precision     |           | not null |
 r_error | double precision     |           |          |
 i_value | double precision     |           | not null |
 i_error | double precision     |           |          |
Indexes:
    "pzd00" PRIMARY KEY, btree (key, row_key)
"""
class PZ_Data(Base):
    __tablename__ = "pz_data"

    key = Column('key', Integer, primary_key=True, nullable=False)
    row_key = Column('row_key', Integer, primary_key=True, nullable=False)
    pztype = Column('type', String(1))
    r_value = Column('r_value', Numeric, nullable=False)
    r_error = Column('r_error', Numeric)
    i_value = Column('i_value', Numeric, nullable=False)
    i_error = Column('i_error', Numeric)

    def __repr__(self):
        return "PZ_Data: key={}, row_key={}, type={}, r_value={}, i_value={}".\
                format(self.key, self.row_key, self.type, self.r_value, self.i_value)


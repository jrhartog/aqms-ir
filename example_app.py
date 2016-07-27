import datetime

from obspy import read_inventory

from sqlalchemy import engine_from_config
from sqlalchemy.orm import sessionmaker

from aqms_ir.configure import configure
#from schema import Base, Abbreviation, Unit, Format, Station
from aqms_ir.schema import Base

from aqms_ir.inv2schema import inventory2db

# Global scope: start the engine and bind a Session factory to it
    
# create configured engine instance
global engine 
engine = engine_from_config(configure(), prefix='sqlalchemy.')

# create a configured "Session" class
Session = sessionmaker(bind=engine)

if __name__ == "__main__":

    import logging

    logging.basicConfig(filename="example_app.log")
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    
    Base.metadata.create_all(engine)

    inv = read_inventory("inventory.xml", format="STATIONXML")

    session = Session()
    inventory2db(session,inv)
    session.close()

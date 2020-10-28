# aqms-ir
WARNING: install psycopg2 first!

Tools to interact with AQMS Instrument Response part of database schema
Uses the obspy Inventory class to store instrument response info

# Installation
* create a virtual python environment using conda or python3, I will show the latter way.
* `python -m venv py3_for_metadata`
* `source py3_for_metadata/bin/activate`
* `pip install git+https://github.com/pnsn/aqms-ir.git`
* you should now have the scripts `getStationXML`, `loadStationXML`, and `deleteStation` in your path.
* to pull in code updates from this repository: `pip install git+https://github.com/pnsn/aqms-ir.git --upgrade`

## getStationXML

```
usage: getStationXML [-h] [-v] [-a] [-f FILENAME] [-s STATION] [-c CHANNEL]
                     [-l LOCATION]
                     [-ws {BGR,EMSC,ETH,GEONET,GFZ,INGV,IPGP,IRIS,ISC,KOERI,LMU,NCEDC,NIEP,NOA,ODC,ORFEUS,RESIF,SCEDC,USGS,USP}]
                     [-level {station,channel,response}]
                     network

Retrieves FDSN StationXML from a fdsn webservice (default=IRIS) and saves
output to a file.

positional arguments:
  network               Specify a FDSN or Virtual network code, wildcards are
                        allowed

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Be more verbose in logfile
  -a, --active          Request metadata for active channels only, default is
                        for all times!
  -f FILENAME, --filename FILENAME
                        Provide output filename, default is inventory.xml
  -s STATION, --station STATION
                        Specify a station code, wildcards are allowed
  -c CHANNEL, --channel CHANNEL
                        Specify a channel code, wildcards are allowed
  -l LOCATION, --location LOCATION
                        Specify a location code, wildcards are allowed
  -ws {BGR,EMSC,ETH,GEONET,GFZ,INGV,IPGP,IRIS,ISC,KOERI,LMU,NCEDC,NIEP,NOA,ODC,ORFEUS,RESIF,SCEDC,USGS,USP}, --webservice {BGR,EMSC,ETH,GEONET,GFZ,INGV,IPGP,IRIS,ISC,KOERI,LMU,NCEDC,NIEP,NOA,ODC,ORFEUS,RESIF,SCEDC,USGS,USP}
                        Specify Webservice to query (default=IRIS)
  -level {station,channel,response}, --level {station,channel,response}
                        Specify level of information (default=response)
```

## loadStationXML
loadStationXML -h

```
usage: loadStationXML [-h] [-v] [-a] [-i] [-p] [-s STATION] [-c CHANNEL]
                      [-l LOCATION]
                      xmlfile

Reads FDSN StationXML and populates (PostgreSQL) AQMS tables station_data,
channel_data, simple_response, channelmap_ampparms, channelmap_codaparms, and
associated dictionary tables (d_abbreviation, d_unit, d_format). It optionally 
will also fill the pz, pzdata, and poles_zeros tables.

Database connection parameters have to be set with environment variables DB_NAME,
DB_HOST, DB_PORT, DB_USER, and optionally, DB_PASSWORD. The tables will be
created if they do not exist yet.  

Logs are written to loadStationXML_YYYY-mm-ddTHH:MM:SS.log. 
See https://github.com/pnsn/aqms_ir

positional arguments:
  xmlfile               Specify name of FDSN StationXML file

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Be more verbose in logfile
  -a, --active          Add currently active channels only
  -i, --inclusive       Load all SOH channels, default is
                        '[BEHS][HLN][123ENZ]' (ignored when -c is provided)
  -p, --pz              also populate poles and zeros (buggy)
  -s STATION, --station STATION
                        Specify a station code, wildcards are allowed
  -c CHANNEL, --channel CHANNEL
                        Specify a channel code, wildcards are allowed
  -l LOCATION, --location LOCATION
                        Specify a location code, wildcards are allowed
```

## deleteStation

```
usage: deleteStation [-h] [-v] network_code station_code

Deletes a station's metadata from (PostgreSQL) AQMS tables station_data,
channel_data, simple_response, channelmap_ampparms, channelmap_codaparms, and
poles_and_zeros related tables. It does not remove any entries from the
various dictionary tables. Database connection parameters have to be set with
environment variables DB_NAME, DB_HOST, DB_PORT, DB_USER, and optionally,
DB_PASSWORD. Logs are written to deleteStation_YYYY-mm-ddTHH:MM:SS.log See
https://github.com/pnsn/aqms_ir

positional arguments:
  network_code   FDSN Network code, e.g. UW, CI, HV
  station_code   Station lookup code, e.g. ASR, PAS, LON, COR

optional arguments:
  -h, --help     show this help message and exit
  -v, --verbose  Be more verbose in logfile
```


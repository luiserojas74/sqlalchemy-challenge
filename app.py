from flask import Flask, jsonify

import numpy as np
import pandas as pd
import datetime as dt
import calendar

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

def substract_year(date):
    one_year_delta = dt.timedelta(days=366 if ((date.month < 3 and calendar.isleap(date.year-1)) or
                                               (date.month >= 3 and calendar.isleap(date.year))) else 365)
    return date - one_year_delta

#################################################
# Database Setup
#################################################
# create engine to hawaii.sqlite
dbpath="sqlite:///Resources/hawaii.sqlite"
engine = create_engine(dbpath)

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

# Save references to each table
# Assign the measurement class to a variable called `Measurement`
Measurement = Base.classes.measurement
# Assign the station class to a variable called `Station`
Station = Base.classes.station

#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Flask Routes
#################################################


@app.route("/")
def list_routes():
    """List all available api routes."""
    return (
        # f"Available Routes:<br/>"
        # f"/api/v1.0/precipitation<br/>"
        # f"/api/v1.0/stations<br/>"
        # f"/api/v1.0/tobs<br/>"
        # f"/api/v1.0/start_date (yyyy-mm-dd) <br/>"
        # f"/api/v1.0/start_date/end_date (yyyy-mm-dd)")

        f"<h2>Welcome to Hawaii Weather and Precipitation Analysis API!!</h2>"
        f"<img src='https://www.fodors.com/wp-content/uploads/2018/11/38_GoList_NorthAmerica_Hawaii_shutterstock_339637010.jpg'"
        f"<br/><br/><h3>Available Routes:</h3>"
        f"<ul>"
        f"<li><a target='blank' href='http://127.0.0.1:5000/api/v1.0/precipitation'>Precipitation data</a><br/>"
        f"<i>Usage: Click on the link or Append /api/v1.0/precipitation to the URL.</i></li><br/>"       
        f"<li><a target='_blank' href='http://127.0.0.1:5000/api/v1.0/stations'>Stations in the dataset</a><br/>"
        f"<i>Usage: Click on the link or Append /api/v1.0/stations to the URL.</i></li><br/>"
        f"<li><a target='_blank' href='http://127.0.0.1:5000/api/v1.0/tobs'>Temperature observations of the most active station for the most recent year in the dataset</a><br/>"
        f"<i>Usage: Click on the link or Append /api/v1.0/tobs to the URL.</i></li><br/>"
        f"<li><a target='_blank' href='http://127.0.0.1:5000/api/v1.0/2010-01-01'>Minimum, average and maximum temperatures for a given start date</a><br/>"
        f"<i>Usage: Append a start date (yyyy-mm-dd) to the URL such as /api/v1.0/startdate. Click on the link for default start date 2010-01-01.<br/>"
        f"Hint: enter dates between 2010-01-01 and 2017-08-23.</i></li><br/>"
        f"<li><a target='_blank' href='http://127.0.0.1:5000/api/v1.0/2010-01-01/2017-08-23'>Minimum, average and maximum temperatures for a given date range</a><br/>"
        f"<i>Usage: Append start and end dates (yyyy-mm-dd/yyyy-mm-dd) to the URL such as /api/v1.0/startdate/enddate. Click on the link for default start-end date range 2010-01-01/2017-08-23.<br/>"
        f"Hint: enter dates between 2010-01-01 and 2017-08-23.</i></li><br/>"
        f"</ul>"
    )


@app.route("/api/v1.0/precipitation")
def precipitation():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a list of Measurement data including date and prcp"""
    # Query all passengers
    results = session.query(Measurement.date, Measurement.prcp).all()

    session.close()

    # Convert the query results to a dictionary using `date` as the key and `prcp` as the value.
    all_measurements = []
    for date, prcp in results:
        measurement_dict = {}
        measurement_dict[date] = prcp
        all_measurements.append(measurement_dict)

    # Return the JSON representation of your dictionary.
    return jsonify(all_measurements)


@app.route("/api/v1.0/stations")
def stations():
    """Return a list of all stations"""

    # Create our session (link) from Python to the DB
    session = Session(engine)

    # Query all stations
    results = session.query(Station.id, Station.station, Station.name).all()

    session.close()

    # Convert list of tuples into normal list
    stations = list(np.ravel(results))
    # Return a JSON list of stations from the dataset.
    return jsonify(stations)


@app.route("/api/v1.0/tobs")
def tobs():
    # Query the dates and temperature observations of the most active station for the last year of data.
    
    # Create our session (link) from Python to the DB
    session = Session(engine)

    # Find the most recent date in the data set.
    latest_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()[0]

    # Calculate the date one year from the last date in data set.
    # Convert string date to date
    datetime_object = dt.datetime.strptime(latest_date, '%Y-%m-%d').date()
    # Substract a year from the lastest date
    a_year_before_latest_date = substract_year(datetime_object)

    # List the stations and the counts in descending order.
    sel = [Station.station,func.count(Measurement.id)]
    active_stations = session.query(*sel).\
        filter(Station.station  == Measurement.station).\
        group_by(Station.station).\
        order_by(func.count(Measurement.id).desc()).all()
    most_active_station_id = active_stations[0][0]

    # Using the most active station id
    # Query the last 12 months of temperature observation data for this station 
    most_active_station_last_year = session.query(Measurement.date, Measurement.tobs).\
        filter(Measurement.date >= a_year_before_latest_date).\
        filter(Measurement.date <= latest_date).\
        filter(Measurement.station == most_active_station_id).all()

    session.close()

    # Return a JSON list of temperature observations (TOBS) for the previous year.
    return jsonify(most_active_station_last_year)

@app.route("/api/v1.0/<start_date>")
def start(start_date):
    # Create our session (link) from Python to the DB
    session = Session(engine)

    sel = [func.min(Measurement.tobs),
        func.avg(Measurement.tobs),
        func.max(Measurement.tobs)]
    most_active_station_temps = session.query(*sel).\
        filter(Measurement.date >= start_date).all()
    
    session.close()
    
    # Return a JSON list of the minimum temperature, the average temperature, and the max temperature for a given start date
    return jsonify(most_active_station_temps)

@app.route("/api/v1.0/<start_date>/<end_date>")
def start_end(start_date,end_date):
    # Create our session (link) from Python to the DB
    session = Session(engine)

    sel = [func.min(Measurement.tobs),
        func.avg(Measurement.tobs),
        func.max(Measurement.tobs)]
    most_active_station_temps = session.query(*sel).\
        filter(Measurement.date >= start_date).\
        filter(Measurement.date <= end_date).all()
    
    session.close()
    
    # Return a JSON list of the minimum temperature, the average temperature, and the max temperature for a given start-end range
    return jsonify(most_active_station_temps)


if __name__ == "__main__":
    app.run(debug=True)

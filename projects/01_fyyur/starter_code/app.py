#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *

import sys
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')

# TODO: connect to a local postgresql database
db = SQLAlchemy(app)
migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#


class Show(db.Model):
    __tablename__ = 'Show'
    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'))
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'))
    start_time = db.Column(db.DateTime, default=datetime.utcnow)

    def dictionary(self):
        return {
            'id': self.id,
            'venue_id': self.venue_id,
            'artist_id': self.artist_id,
            'start_time': self.start_time
        }


class Venue(db.Model):
    __tablename__ = 'Venue'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    webpage_link = db.Column(db.String(500))
    genres = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    seeking_talent = db.Column(db.Boolean(), nullable=False, default=False)
    shows = db.relationship('Artist', secondary='Show')

    def dictionary(self):
        return {
            'id': self.id,
            'name': self.name,
            'city': self.city,
            'state': self.state,
            'phone': self.phone,
            'genres': self.genres.split(','),  # convert string to list
            'image_link': self.image_link,
            'facebook_link': self.facebook_link,
            'webpage_link': self.webpage_link,
            'seeking_talent': self.seeking_talent,
            'seeking_description': self.description,
        }
        # add shows (venue has many shows)


class Artist(db.Model):
    __tablename__ = 'Artist'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    webpage_link = db.Column(db.String(500))
    description = db.Column(db.String(500), nullable=True)
    seeking_venue = db.Column(db.Boolean(), nullable=False, default=False)
    shows = db.relationship('Venue', secondary='Show')

    def dictionary(self):
        return {
            'id': self.id,
            'name': self.name,
            'city': self.city,
            'state': self.state,
            'phone': self.phone,
            'genres': self.genres.split(','),  # convert string to list
            'image_link': self.image_link,
            'facebook_link': self.facebook_link,
            'webpage_link': self.webpage_link,
            'seeking_venue': self.seeking_venue,
            'seeking_description': self.description,
        }
        # add shows (artist has many shows)

        # TODO: implement any missing fields, as a database migration using Flask-Migrate

        # TODO: implement any missing fields, as a database migration using Flask-Migrate

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    # TODO: replace with real venues data.
    #       num_shows should be aggregated based on number of upcoming shows per venue.
    city_state = db.session.query(Venue.state, Venue.city).group_by(
        Venue.state, Venue.city).all()

    currentdate = datetime.today()
    data = []
    for g in city_state:
        res = {
            'state': g[0],
            'city': g[1],
        }
        venues = db.session.query(Venue).filter(
            (Venue.state == g[0]) & (Venue.city == g[1])).all()
        venuesData = []
        for v in venues:
            NumOfUpcomingShows = db.session.query(Show).filter(
                (Show.start_time > currentdate) & (Show.venue_id == v.id)).count()
            venueData = {
                'id': v.id,
                'name': v.name,
                'num_upcoming_shows': NumOfUpcomingShows
            }
            venuesData.append(venueData)
            res['venues'] = venuesData
        data.append(res)
    return render_template('pages/venues.html', areas=data)
    # data=[{
    #   "city": "San Francisco",
    #   "state": "CA",
    #   "venues": [{
    #     "id": 1,
    #     "name": "The Musical Hop",
    #     "num_upcoming_shows": 0,
    #   }, {
    #     "id": 3,
    #     "name": "Park Square Live Music & Coffee",
    #     "num_upcoming_shows": 1,
    #   }]
    # }, {
    #   "city": "New York",
    #   "state": "NY",
    #   "venues": [{
    #     "id": 2,
    #     "name": "The Dueling Pianos Bar",
    #     "num_upcoming_shows": 0,
    #   }]
    # }]
    # return render_template('pages/venues.html', areas=data);


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    term =request.form.get('search_term', '').lower()
    venues = Venue.query.filter(Venue.name.ilike(f'%{term}%')).all()
    venues_response = []
    today = datetime.today()
    for v in venues:
        upcoming_shows_count = db.session.query(Show).join(Venue).filter(Show.start_time > today).count()
        venues_response.append({
            "id": v.id,
            "name": v.name,
            "num_upcoming_shows": upcoming_shows_count
        })
    response = {
        "count": Venue.query.filter(Venue.name.ilike(f'%{term}%')).count(),
        "data": venues_response
    }
    # [{
    #         "id": 2,
    #         "name": "The Dueling Pianos Bar",
    #         "num_upcoming_shows": 0,
    #     }]
    return render_template('pages/search_venues.html', results=response, search_term=term)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    # data1={
    #   "id": 1,
    #   "name": "The Musical Hop",
    #   "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
    #   "address": "1015 Folsom Street",
    #   "city": "San Francisco",
    #   "state": "CA",
    #   "phone": "123-123-1234",
    #   "website": "https://www.themusicalhop.com",
    #   "facebook_link": "https://www.facebook.com/TheMusicalHop",
    #   "seeking_talent": True,
    #   "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
    #   "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60",
    #   "past_shows": [{
    #     "artist_id": 4,
    #     "artist_name": "Guns N Petals",
    #     "artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
    #     "start_time": "2019-05-21T21:30:00.000Z"
    #   }],
    #   "upcoming_shows": [],
    #   "past_shows_count": 1,
    #   "upcoming_shows_count": 0,
    # }
    # data2={
    #   "id": 2,
    #   "name": "The Dueling Pianos Bar",
    #   "genres": ["Classical", "R&B", "Hip-Hop"],
    #   "address": "335 Delancey Street",
    #   "city": "New York",
    #   "state": "NY",
    #   "phone": "914-003-1132",
    #   "website": "https://www.theduelingpianos.com",
    #   "facebook_link": "https://www.facebook.com/theduelingpianos",
    #   "seeking_talent": False,
    #   "image_link": "https://images.unsplash.com/photo-1497032205916-ac775f0649ae?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=750&q=80",
    #   "past_shows": [],
    #   "upcoming_shows": [],
    #   "past_shows_count": 0,
    #   "upcoming_shows_count": 0,
    # }
    # data3={
    #   "id": 3,
    #   "name": "Park Square Live Music & Coffee",
    #   "genres": ["Rock n Roll", "Jazz", "Classical", "Folk"],
    #   "address": "34 Whiskey Moore Ave",
    #   "city": "San Francisco",
    #   "state": "CA",
    #   "phone": "415-000-1234",
    #   "website": "https://www.parksquarelivemusicandcoffee.com",
    #   "facebook_link": "https://www.facebook.com/ParkSquareLiveMusicAndCoffee",
    #   "seeking_talent": False,
    #   "image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
    #   "past_shows": [{
    #     "artist_id": 5,
    #     "artist_name": "Matt Quevedo",
    #     "artist_image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
    #     "start_time": "2019-06-15T23:00:00.000Z"
    #   }],
    #   "upcoming_shows": [{
    #     "artist_id": 6,
    #     "artist_name": "The Wild Sax Band",
    #     "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    #     "start_time": "2035-04-01T20:00:00.000Z"
    #   }, {
    #     "artist_id": 6,
    #     "artist_name": "The Wild Sax Band",
    #     "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    #     "start_time": "2035-04-08T20:00:00.000Z"
    #   }, {
    #     "artist_id": 6,
    #     "artist_name": "The Wild Sax Band",
    #     "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    #     "start_time": "2035-04-15T20:00:00.000Z"
    #   }],
    #   "past_shows_count": 1,
    #   "upcoming_shows_count": 1,
    # }
    venue = Venue.query.get(venue_id)
    # db.session.query(Venue).filter((Venue.state == g[0]) & (Venue.city == g[1])).all()
    today = datetime.today()
    upcoming_shows = db.session.query(Show).filter(
        (Show.venue_id == venue.id) & (Show.start_time >= today)).all()
    past_shows = db.session.query(Show).filter(
        (Show.venue_id == venue.id) & (Show.start_time < today)).all()
    venue_dto = venue.dictionary()
    # data = list(filter(lambda d: d['id'] == venue_id, [data1, data2, data3]))[0]
    upcoming_shows_list = []
    past_shows_list = []
    for show in upcoming_shows:
        artist = Artist.query.get(show.artist_id)
        show = {
            "artist_id": artist.id,
            "artist_name": artist.name,
            "artist_image_link": artist.image_link,
            "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
        }
        upcoming_shows_list.append(show)
    for show in past_shows:
        artist = Artist.query.get(show.artist_id)
        show = {
            "artist_id": artist.id,
            "artist_name": artist.name,
            "artist_image_link": artist.image_link,
            "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
        }
        past_shows_list.append(show)
    NumOfUpcomingShows = db.session.query(Show).filter(
        (Show.start_time >= today) & (Show.venue_id == venue.id)).count()
    NumOfPastShows = db.session.query(Show).filter(
        (Show.start_time < today) & (Show.venue_id == venue.id)).count()

    venue_dto['upcoming_shows'] = upcoming_shows_list
    venue_dto['past_shows'] = past_shows_list
    venue_dto['upcoming_shows_count'] = NumOfUpcomingShows
    venue_dto['past_shows_count'] = NumOfPastShows
    return render_template('pages/show_venue.html', venue=venue_dto)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    form = VenueForm()
    error = False
    try:
        venue = Venue()
        venue.name = request.form['name']
        venue.city = request.form['city']
        venue.state = request.form['state']
        venue.phone = request.form['phone']
        venue.address = request.form['address']
        tmp_genres = request.form.getlist('genres')
        venue.genres = ','.join(tmp_genres)
        venue.webpage_link = request.form['webpage_link']
        venue.image_link = request.form['image_link']
        venue.facebook_link = request.form['facebook_link']
        venue.description = request.form['description']
        venue.seeking_talent = True
        if not venue.description:
            venue.seeking_talent = False
        db.session.add(venue)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
        if error:
            flash('An error occurred. Artist ' +
                  request.form['name'] + ' could not be listed.')
        else:
            flash('Venue ' + request.form['name'] +
                  ' was successfully listed!')
        return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    return None

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    # TODO: replace with real data returned from querying the database
    return render_template('pages/artists.html', artists=Artist.query.all())


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    term =request.form.get('search_term', '').lower()
    artists = Artist.query.filter(Artist.name.ilike(f'%{term}%')).all()
    artists_response = []
    today = datetime.today()
    for v in artists:
        upcoming_shows_count = db.session.query(Show).join(Artist).filter(Show.start_time > today).count()
        artists_response.append({
            "id": v.id,
            "name": v.name,
            "num_upcoming_shows": upcoming_shows_count
        })
    response = {
        "count": Artist.query.filter(Artist.name.ilike(f'%{term}%')).count(),
        "data": artists_response
    }
    # [{
    #         "id": 2,
    #         "name": "The Dueling Pianos Bar",
    #         "num_upcoming_shows": 0,
    #     }]
    
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    artist = Artist.query.get(artist_id)
    # db.session.query(Venue).filter((Venue.state == g[0]) & (Venue.city == g[1])).all()
    today = datetime.today()
    upcoming_shows = db.session.query(Show).filter(
        (Show.artist_id == artist.id) & (Show.start_time >= today)).all()
    past_shows = db.session.query(Show).filter(
        (Show.artist_id == artist.id) & (Show.start_time < today)).all()
    artist_dto = artist.dictionary()
    # data = list(filter(lambda d: d['id'] == venue_id, [data1, data2, data3]))[0]
    upcoming_shows_list = []
    past_shows_list = []
    for s in upcoming_shows:
        venue = Venue.query.get(s.venue_id)
        show = {
            "venue_id": venue.id,
            "venue_name": venue.name,
            "venue_image_link": venue.image_link,
            "start_time": s.start_time.strftime("%m/%d/%Y, %H:%M:%S")
        }
        print(show)
        upcoming_shows_list.append(show)
    for s in past_shows:
        venue = Venue.query.get(s.venue_id)
        show = {
            "venue_id": venue.id,
            "venue_name": venue.name,
            "venue_image_link": venue.image_link,
            "start_time": s.start_time.strftime("%m/%d/%Y, %H:%M:%S")
        }
        print(show)
        past_shows_list.append(show)
    NumOfUpcomingShows = db.session.query(Show).filter(
        (Show.start_time >= today) & (Show.artist_id == artist.id)).count()
    NumOfPastShows = db.session.query(Show).filter(
        (Show.start_time < today) & (Show.artist_id == artist.id)).count()

    artist_dto['upcoming_shows'] = upcoming_shows_list
    artist_dto['past_shows'] = past_shows_list
    artist_dto['upcoming_shows_count'] = NumOfUpcomingShows
    artist_dto['past_shows_count'] = NumOfPastShows
    #data = list(filter(lambda d: d['id'] == artist_id, [data1, data2, data3]))[0]
    #   return jsonify(artist_dto)
    return render_template('pages/show_artist.html', artist=artist_dto)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = {
        "id": 4,
        "name": "Guns N Petals",
        "genres": ["Rock n Roll"],
        "city": "San Francisco",
        "state": "CA",
        "phone": "326-123-5000",
        "website": "https://www.gunsnpetalsband.com",
        "facebook_link": "https://www.facebook.com/GunsNPetals",
        "seeking_venue": True,
        "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
        "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80"
    }
    # TODO: populate form with fields from artist with ID <artist_id>
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = {
        "id": 1,
        "name": "The Musical Hop",
        "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
        "address": "1015 Folsom Street",
        "city": "San Francisco",
        "state": "CA",
        "phone": "123-123-1234",
        "website": "https://www.themusicalhop.com",
        "facebook_link": "https://www.facebook.com/TheMusicalHop",
        "seeking_talent": True,
        "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
        "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
    }
    # TODO: populate form with values from venue with ID <venue_id>
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    form = ArtistForm()
    error = False
    try:
        artist = Artist()
        artist.name = request.form['name']
        artist.city = request.form['city']
        artist.state = request.form['state']
        artist.phone = request.form['phone']
        tmp_genres = request.form.getlist('genres')
        artist.genres = ','.join(tmp_genres)
        artist.webpage_link = request.form['webpage_link']
        artist.image_link = request.form['image_link']
        artist.facebook_link = request.form['facebook_link']
        artist.description = request.form['description']
        artist.seeking_venue = True
        if not artist.description:
            artist.seeking_venue = False
        db.session.add(artist)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
        if error:
            flash('An error occurred. Artist ' +
                  request.form['name'] + ' could not be listed.')
        else:
            flash('Artist ' + request.form['name'] +
                  ' was successfully listed!')
        return render_template('pages/home.html')
# @app.route('/artists/create', methods=['POST'])
# def create_artist_submission():
#   # called upon submitting the new artist listing form
#   # TODO: insert form data as a new Venue record in the db, instead
#   # TODO: modify data to be the data object returned from db insertion

#   # on successful db insert, flash success
#   flash('Artist ' + request.form['name'] + ' was successfully listed!')
#   # TODO: on unsuccessful db insert, flash an error instead.
#   # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
#   return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    #       num_shows should be aggregated based on number of upcoming shows per venue.
    
    shows = Show.query.all()
    shows_dtos = []
    for show in shows:
        show_dto = show.dictionary()
        venue = Venue.query.get(show.venue_id)
        artist = Artist.query.get(show.artist_id)
        show_dto['venue_name'] = venue.name
        show_dto['artist_name'] = artist.name
        show_dto['artist_image_link'] = artist.image_link
        show_dto['start_time'] = show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
        shows_dtos.append(show_dto)
    return render_template('pages/shows.html', shows=shows_dtos)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead
    form = ShowForm()
    error = False
    try:
        show = Show()
        show.artist_id = request.form['artist_id']
        show.venue_id = request.form['venue_id']
        show.start_time = request.form['start_time']
        db.session.add(show)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
        if error:
            flash('An error occurred. Artist ' +
                  request.form['name'] + ' could not be listed.')
        else:
            # on successful db insert, flash success
            # TODO: on unsuccessful db insert, flash an error instead.
            # e.g., flash('An error occurred. Show could not be listed.')
            # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
            flash('Show was successfully listed!')
    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
# if __name__ == '__main__':
#     app.run()
if __name__ == '__main__':
    manager.run()
# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''

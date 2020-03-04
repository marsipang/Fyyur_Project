#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
import dateutil.parser
import babel, logging
from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from logging import Formatter, FileHandler
from forms import VenueForm, ArtistForm, ShowForm, AlbumForm, SongForm
from sqlalchemy.sql import func
from sqlalchemy import case, inspect
from datetime import datetime
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#
app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#
venue_genres = db.Table('venue_genres',
    db.Column('venue_id', db.Integer, db.ForeignKey('Venue.id', onupdate="CASCADE", ondelete="CASCADE"), primary_key=True),
    db.Column('genre_id', db.Integer, db.ForeignKey('Genre.id'), primary_key=True)
)

artist_genres = db.Table('artist_genres',
    db.Column('artist_id', db.Integer, db.ForeignKey('Artist.id'), primary_key=True),
    db.Column('genre_id', db.Integer, db.ForeignKey('Genre.id'), primary_key=True)
)

class Genre(db.Model):
    __tablename__ = 'Genre'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True)

    def __repr__(self):
        return f'<{self.id} {self.name}>'
    
class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500), nullable=True)
    facebook_link = db.Column(db.String(120), nullable=True)
    website = db.Column(db.String(120), nullable=True)
    seeking_talent = db.Column(db.Boolean, nullable=False)
    seeking_description = db.Column(db.String, nullable=True)
    shows = db.relationship('Show', backref='venue')
    genres = db.relationship('Genre', secondary=venue_genres, cascade='all, delete',
                             backref=db.backref('genres', lazy=True))
    
    def __repr__(self):
        return f'<{self.id} {self.name}>'
    
    def upcoming_show_count(self):
        return sum([1 if i.upcoming_show() else 0 for i in self.shows])
    
    def past_show_count(self):
        return sum([0 if i.upcoming_show() else 1 for i in self.shows])
    
    def venue_dict(self):
        dict_obj = {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}
        dict_obj['genres'] = [i.name for i in self.genres]
        dict_obj['genre_ids'] = [i.id for i in self.genres]
        dict_obj['upcoming_shows_count'] = self.upcoming_show_count()
        dict_obj['past_shows_count'] = self.past_show_count()
        dict_obj['past_shows'] = [i.show_dict() for i in self.shows if i.upcoming_show() == False]
        dict_obj['upcoming_shows'] = [i.show_dict() for i in self.shows if i.upcoming_show()]
        return dict_obj

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500), nullable=True)
    facebook_link = db.Column(db.String(120), nullable=True)
    website = db.Column(db.String(120), nullable=True)
    seeking_venue = db.Column(db.Boolean, nullable=False)
    seeking_description = db.Column(db.String, nullable=True)
    shows = db.relationship('Show', backref='artist')
    genres = db.relationship('Genre', secondary=artist_genres,
                             backref=db.backref('artistgenres', lazy=True))
    albums = db.relationship('Album', backref='album')
    songs = db.relationship('Song', backref='song')
    
    def __repr__(self):
        return f'<{self.id} {self.name}>'

    def upcoming_show_count(self):
        return sum([1 if i.upcoming_show() else 0 for i in self.shows])
    
    def past_show_count(self):
        return sum([0 if i.upcoming_show() else 1 for i in self.shows])
    
    def artist_dict(self):
        dict_obj = {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}
        dict_obj['genres'] = [i.name for i in self.genres]
        dict_obj['genre_ids'] = [i.id for i in self.genres]
        dict_obj['upcoming_shows_count'] = self.upcoming_show_count()
        dict_obj['past_shows_count'] = self.past_show_count()
        dict_obj['past_shows'] = [i.show_dict() for i in self.shows if i.upcoming_show() == False]
        dict_obj['upcoming_shows'] = [i.show_dict() for i in self.shows if i.upcoming_show()]
        dict_obj['albums'] = [i.album_dict() for i in self.albums]
        dict_obj['songs'] = [i.name for i in self.songs if i.album_id == None]
        return dict_obj

class Show(db.Model):
    __tablename__ = 'Show'
    
    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'))
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'))
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    
    def __repr__(self):
        return f'<{self.id} {self.venue_id} {self.start_time}>'
    
    def upcoming_show(self):
        if self.start_time >= datetime.now():
            return True
        else:
            return False
    
    def show_dict(self):
        venue_dict = {'venue_' + c.key: getattr(self.venue, c.key) for c in inspect(self.venue).mapper.column_attrs}
        artist_dict = {'artist_' + c.key: getattr(self.artist, c.key) for c in inspect(self.artist).mapper.column_attrs}
        dict_obj = {**venue_dict, **artist_dict}
        dict_obj['start_time'] = self.start_time.strftime('%Y-%m-%d %H:%M:%S')
        return dict_obj
    
class Album(db.Model):
    __tablename__ = 'Album'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    release_date = db.Column(db.DateTime, nullable=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=True)
    songs = db.relationship('Song', backref='albumsong')
    
    def __repr__(self):
        return f'<{self.id} {self.name}>'

    def album_dict(self):
        dict_obj = {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}
        dict_obj['release_date'] = self.release_date.strftime('%Y-%m-%d %H:%M:%S')
        dict_obj['songs'] = [i.name for i in self.songs]
        return dict_obj

class Song(db.Model):
    __tablename__ = 'Song'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    release_date = db.Column(db.DateTime, nullable=True)
    album_id = db.Column(db.Integer, db.ForeignKey('Album.id'), nullable=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'))
    
    def __repr__(self):
        return f'<{self.id} {self.name}>'

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en_US.UTF-8')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
    #get the most recently listed 5 venues
    venue_data = Venue.query.order_by(Venue.id.desc()).limit(5).all()
    venues = [i.venue_dict() for i in venue_data]
    #get the most recently listed 5 artists
    artist_data = Artist.query.order_by(Artist.id.desc()).limit(5).all()
    artists = [i.artist_dict() for i in artist_data]
    return render_template('pages/home.html', venues=venues, artists=artists)


#  Venues
#  ----------------------------------------------------------------
@app.route('/venues')
def venues():
    #get distinct city and states of venues
    data = [{"city":i.city, 
             "state":i.state
             } for i in Venue.query.distinct('city', 'state').order_by('state', 'city').all()]
    #for each distinct city and state, get data of the venues in those city/state
    for i in range(0, len(data)):
        data[i]['venues'] = [{"id": j.id,
            "name": j.name,
            "num_upcoming_shows": j.num_upcoming_shows
            } for j in db.session.query(Venue.id, Venue.name, func.sum(case([(Show.start_time > func.now(), 1)], else_=0)).label('num_upcoming_shows')).outerjoin(Show).filter(Venue.city==data[i]['city']).group_by(Venue).order_by('name').all()]
    return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    search_term = request.form.get('search_term', '')
    response = {'data':[i.venue_dict() for i in Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()]}
    response['count'] = len(response['data'])
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    venue_data = Venue.query.get(venue_id)
    data = venue_data.venue_dict()
    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------
@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    #render form
    form = VenueForm()
    #get the genres that are in the database and put them as the choices for the genre part of the form
    genre_choices = Genre.query.order_by('name').all()
    form.genres.choices = [(i.id, i.name) for i in genre_choices] + [(0, 'Other')]
    return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    #render form
    form = VenueForm(request.form)
    #get the genres that are in the database and put them as the choices for the genre part of the form
    genre_choices = Genre.query.order_by('name').all()
    form.genres.choices = [(i.id, i.name) for i in genre_choices] + [(0, 'Other')]
    error = False   
    if form.validate_on_submit():
        try:
            #get table objects of the selected genres
            genre_data = Genre.query.filter(Genre.id.in_(form.genres.data)).order_by('id').all()
            #enter new genre into database
            if 0 in form.genres.data:
                new_genre = Genre(name = form.other_genre.data)
                genre_data = genre_data + [new_genre]
            #enter a new venue into database
            venue = Venue(name = form.name.data,
                          city = form.city.data,
                          state = form.state.data,
                          address = form.address.data,
                          phone = form.phone.data,
                          image_link = form.image_link.data,
                          facebook_link = form.facebook_link.data,
                          genres = genre_data,
                          website = form.website.data,
                          seeking_talent = form.seeking_talent.data,
                          seeking_description = form.seeking_description.data
                          )
            db.session.add(venue)
            db.session.commit()
        except:
            db.session.rollback()
            error = True
        finally:
            db.session.close()
        if error:
            # if there's an error, flash message and stay on page
            flash('An error occurred. Venue ' + form.name.data + ' could not be listed.')
            return render_template('forms/new_venue.html', form=form)
        else:
            # on successful db insert, flash success and take to home page
            flash('Venue ' + request.form['name'] + ' was successfully listed!')
            return render_template('pages/home.html')
    else:
        # if form doesn't pass validation, flash message and stay on page
        flash('An error occurred. Venue ' + form.name.data + ' could not be listed.')
        return render_template('forms/new_venue.html', form=form)
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
      
#  Delete Venue
#  ----------------------------------------------------------------
@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    try:
        #find venue record to delete and delete
        venue = db.session.query(Venue).get(venue_id)
        db.session.delete(venue)
        db.session.commit()
        result = {'success': True}
    except:
        db.session.rollback()
        result = {'success': False}
    finally:
        db.session.close()
    #return result so the page can either error or reroute
    return jsonify(result)

#  Update Venue
#  ----------------------------------------------------------------
@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    #render form
    form = VenueForm()
    #get the genres that are in the database and put them as the choices for the genre part of the form
    genre_choices = Genre.query.order_by('name').all()
    form.genres.choices = [(i.id, i.name) for i in genre_choices] + [(0, 'Other')]
    venue = Venue.query.get(venue_id)
    #populating form with values from venue
    form.name.default = venue.name
    form.genres.default = [i.id for i in venue.genres]
    form.address.default = venue.address
    form.city.default = venue.city
    form.state.default = venue.state
    form.phone.default = venue.phone
    form.website.default = venue.website
    form.facebook_link.default = venue.facebook_link
    form.seeking_talent.default = venue.seeking_talent
    form.seeking_description.default = venue.seeking_description
    form.image_link.default = venue.image_link
    form.process()
    return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    #render form
    form = VenueForm(request.form)
    #get the genres that are in the database and put them as the choices for the genre part of the forms
    genre_choices = Genre.query.order_by('name').all()
    form.genres.choices = [(i.id, i.name) for i in genre_choices] + [(0, 'Other')]
    venue = Venue.query.get(venue_id)
    error = False 
    if form.validate_on_submit():
        try:
            #get table objects of the selected genres
            genre_data = Genre.query.filter(Genre.id.in_(form.genres.data)).order_by('id').all()
            #update venue record
            venueobj = db.session.query(Venue).get(venue_id)
            venueobj.name = form.name.data
            venueobj.city = form.city.data
            venueobj.state = form.state.data
            venueobj.address = form.address.data
            venueobj.phone = form.phone.data
            venueobj.image_link= form.image_link.data
            venueobj.facebook_link = form.facebook_link.data
            venueobj.genres = genre_data
            venueobj.website = form.website.data
            venueobj.seeking_talent = form.seeking_talent.data
            venueobj.seeking_description = form.seeking_description.data
            #if there's a new genre, add it to the database and then update venue record to have it
            if 0 in form.genres.data:
                new_genre = Genre(name = form.other_genre.data)
                db.session.add(new_genre)
                venueobj.genres.append(new_genre)
            db.session.commit()
        except:
            db.session.rollback()
            error = True
        finally:
            db.session.close()
        if error:
            #if there's an error, flash message and stay on page
            flash('An error occurred. Venue ' + form.name.data + ' could not be edited.')
            return render_template('forms/edit_venue.html', form=form, venue=venue)
        else:
            #if success, reroute to the venue page
            return redirect(url_for('show_venue', venue_id=venue_id))
    else:
        return render_template('forms/edit_venue.html', form=form, venue=venue)

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    #get all artists
    data = Artist.query.order_by('name').all()
    return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    search_term = request.form.get('search_term', '')
    response = {'data':[i.artist_dict() for i in Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()]}
    response['count'] = len(response['data'])
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  artist_data = Artist.query.get(artist_id)
  data = artist_data.artist_dict()
  return render_template('pages/show_artist.html', artist=data)

#  Create Artist
#  ----------------------------------------------------------------
@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    #render form
    form = ArtistForm()
    #get the genres that are in the database and put them as the choices for the genre part of the form
    genre_choices = Genre.query.order_by('name').all()
    form.genres.choices = [(i.id, i.name) for i in genre_choices] + [(0, 'Other')]
    return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    #render form
    form = ArtistForm(request.form)
    #get the genres that are in the database and put them as the choices for the genre part of the form
    genre_choices = Genre.query.order_by('name').all()
    form.genres.choices = [(i.id, i.name) for i in genre_choices] + [(0, 'Other')]
    error = False   
    if form.validate_on_submit():
        try:
            #get table objects of the selected genres
            genre_data = Genre.query.filter(Genre.id.in_(form.genres.data)).order_by('id').all()
            #if there's a new genre, add it to the database
            if 0 in form.genres.data:
                new_genre = Genre(name = form.other_genre.data)
                genre_data = genre_data + [new_genre]
            #create new artist record in database
            artist = Artist(name = form.name.data,
                          city = form.city.data,
                          state = form.state.data,
                          phone = form.phone.data,
                          image_link = form.image_link.data,
                          facebook_link = form.facebook_link.data,
                          genres = genre_data,
                          website = form.website.data,
                          seeking_venue = form.seeking_venue.data,
                          seeking_description = form.seeking_description.data
                          )  
            db.session.add(artist)
            db.session.commit()
        except:
            db.session.rollback()
            error = True
        finally:
            db.session.close()
        if error:
            #if error, flash message and stay on page
            flash('An error occurred. Artist ' + form.name.data + ' could not be listed.')
            return render_template('forms/new_artist.html', form=form)
        else:
            # on successful db insert, flash success and display home page
            flash('Artist ' + request.form['name'] + ' was successfully listed!')
            return render_template('pages/home.html')
    else:
        #if form isn't valid, flash message and stay on page
        flash('An error occurred. Artist ' + form.name.data + ' could not be listed.')
        return render_template('forms/new_artist.html', form=form)  
    
#  Update Artist
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    #render form
    form = ArtistForm()
    #get the genres that are in the database and put them as the choices for the genre part of the form
    genre_choices = Genre.query.order_by('name').all()
    form.genres.choices = [(i.id, i.name) for i in genre_choices] + [(0, 'Other')]
    artist = Artist.query.get(artist_id)
    #populating form with values from Artist
    form.name.default = artist.name
    form.genres.default = [i.id for i in artist.genres]
    form.city.default = artist.city
    form.state.default = artist.state
    form.phone.default = artist.phone
    form.website.default = artist.website
    form.facebook_link.default = artist.facebook_link
    form.seeking_venue.default = artist.seeking_venue
    form.seeking_description.default = artist.seeking_description
    form.image_link.default = artist.image_link
    form.process()
    return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    #render form
    form = ArtistForm(request.form)
    #get the genres that are in the database and put them as the choices for the genre part of the form
    genre_choices = Genre.query.order_by('name').all()
    form.genres.choices = [(i.id, i.name) for i in genre_choices] + [(0, 'Other')]
    artist = Artist.query.get(artist_id)
    error = False 
    if form.validate_on_submit():
        try:
            #get table objects of the selected genres
            genre_data = Genre.query.filter(Genre.id.in_(form.genres.data)).order_by('id').all()
            #update artist record in database
            artistobj = db.session.query(Artist).get(artist_id)
            artistobj.name = form.name.data
            artistobj.city = form.city.data
            artistobj.state = form.state.data
            artistobj.phone = form.phone.data
            artistobj.image_link= form.image_link.data
            artistobj.facebook_link = form.facebook_link.data
            artistobj.genres = genre_data
            artistobj.website = form.website.data
            artistobj.seeking_venue = form.seeking_venue.data
            artistobj.seeking_description = form.seeking_description.data
            #if there's a new genre, add it to the database and then update artist record to have it
            if 0 in form.genres.data:
                new_genre = Genre(name = form.other_genre.data)
                db.session.add(new_genre)
                artistobj.genres.append(new_genre)
            db.session.commit()
        except:
            db.session.rollback()
            error = True
        finally:
            db.session.close()
        if error:
            #if error, flash message and stay on page
            flash('An error occurred. Artist ' + form.name.data + ' could not be edited.')
            return render_template('forms/edit_artist.html', form=form, artist=artist)
        else:
            #if success, reroute to artist page
            return redirect(url_for('show_artist', artist_id=artist_id))
    else:
        return render_template('forms/edit_artist.html', form=form, artist=artist)  

#  Shows
#  ----------------------------------------------------------------
@app.route('/shows')
def shows():
  # displays list of shows at /shows
  data = [i.show_dict() for i in Show.query.all()]        
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    #render form
    form = ShowForm(request.form)
    error = False   
    if form.validate_on_submit():
        #check to make sure the selected times for the selected venue don't overlap with a booking 
        #for that venue already. If it is, then flash message and stay on page
        if db.session.query(db.exists().where((Show.venue_id == form.venue_id.data) &
        (((form.start_time.data >= Show.start_time) &
        (form.start_time.data <= Show.end_time)) |
        ((form.end_time.data >= Show.start_time) &
        (form.end_time.data <= Show.end_time)) |
        (Show.start_time.between(form.start_time.data, form.end_time.data)) |
        (Show.end_time.between(form.start_time.data, form.end_time.data))
        ))).scalar():
            flash('''The venue is unavailable during the entered times, please check availability on the Venue's page''')
            return render_template('forms/new_show.html', form=form)
        #check to make sure the selected times for the selected artist don't overlap with a booking 
        #for that artist already. If it is, then flash message and stay on page
        elif db.session.query(db.exists().where((Show.artist_id == form.artist_id.data) &
        (((form.start_time.data >= Show.start_time) &
        (form.start_time.data <= Show.end_time)) |
        ((form.end_time.data >= Show.start_time) &
        (form.end_time.data <= Show.end_time)) |
        (Show.start_time.between(form.start_time.data, form.end_time.data)) |
        (Show.end_time.between(form.start_time.data, form.end_time.data))
        ))).scalar():
            flash('''The artist is unavailable during the entered times, please check availability on the Artist's page''')
            return render_template('forms/new_show.html', form=form)
        else:
            try:
                #if show isn't overlapping and can be booked, then create record for show and put in database
                show = Show(venue_id = form.venue_id.data,
                            artist_id = form.artist_id.data,
                            start_time = form.start_time.data,
                            end_time = form.end_time.data
                            )
                db.session.add(show)
                db.session.commit()
            except:
                db.session.rollback()
                error = True
            finally:
                db.session.close()
            if error:
                #if there's an error, flash message and stay on page
                flash('An error occurred. Show could not be listed.')
                return render_template('forms/new_show.html', form=form)
            else:
                # on successful db insert, flash success and show home page
                flash('Show was successfully listed!')
                return render_template('pages/home.html')
    else:
        flash('An error occurred. Show could not be listed.')
        return render_template('forms/new_show.html', form=form)   

#  Albums
#  ----------------------------------------------------------------
@app.route('/artist/<artist_id>/create_album')
def create_album(artist_id):
    # renders form
    form = AlbumForm()
    #default artist_id field to the artist_id the page was clicked in through
    form.artist_id.default = artist_id
    form.process()
    return render_template('forms/new_album.html', form=form)

@app.route('/artist/<artist_id>/create_album', methods=['POST'])
def create_album_submission(artist_id):
    # called to create new albums in the db, upon submitting new album listing form
    #render form
    form = AlbumForm(request.form)
    error = False   
    if form.validate_on_submit():
        try:
            #create record for album in database
            album = Album(artist_id = form.artist_id.data,
                          name = form.name.data,
                          release_date = form.release_date.data
                          )
            db.session.add(album)
            db.session.commit()
        except:
            db.session.rollback()
            error = True
        finally:
            db.session.close()
        if error:
            #if error, flash message and stay on page
            flash('An error occurred. Album could not be listed.')
            return render_template('forms/new_album.html', form=form)
        else:
            #if success, reroute to the album's artist's page
            return redirect(url_for('show_artist', artist_id=form.artist_id.data))
    else:
        flash('An error occurred. Show could not be listed.')
        return render_template('forms/new_album.html', form=form)   

#  Songs
#  ----------------------------------------------------------------
@app.route('/artist/<artist_id>/create_song')
def create_song(artist_id):
    # renders form. do not touch.
    #render form
    form = SongForm()
    #default artist_id field to the artist_id the page was clicked in through
    form.artist_id.default = artist_id
    form.process()
    return render_template('forms/new_song.html', form=form)

@app.route('/artist/<artist_id>/create_song', methods=['POST'])
def create_song_submission(artist_id):
    # called to create new albums in the db, upon submitting new album listing form
    #render form
    form = SongForm(request.form)
    error = False   
    if form.validate_on_submit():
        try:
            #if there is an album_id entered, then create song record in database with the album_id
            if form.album_id.data == '':
                song = Song(artist_id = form.artist_id.data,
                        name = form.name.data,
                        release_date = form.release_date.data
                        )
            #if there is no album_id entered, then create song record in database with album_id set to Null
            else:
                song = Song(artist_id = form.artist_id.data,
                            album_id = form.album_id.data,
                            name = form.name.data,
                            release_date = form.release_date.data
                            )
            db.session.add(song)
            db.session.commit()
        except:
            db.session.rollback()
            error = True
        finally:
            db.session.close()
        if error:
            #if error, flash message and stay on page
            flash('An error occurred. Song could not be listed.')
            return render_template('forms/new_song.html', form=form)
        else:
            #if success, reroute to the song's artist's page
            return redirect(url_for('show_artist', artist_id=form.artist_id.data))
    else:
        flash('An error occurred. Show could not be listed.')
        return render_template('forms/new_song.html', form=form)   

#  Error Handlers
#  ----------------------------------------------------------------
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''

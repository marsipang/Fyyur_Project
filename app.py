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
from forms import VenueForm, ArtistForm, ShowForm
from sqlalchemy.sql import func
from sqlalchemy import case, inspect
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
    name = db.Column(db.String)

    def __repr__(self):
        return f'<{self.id} {self.name}>'

from datetime import datetime

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
        return dict_obj

class Show(db.Model):
    __tablename__ = 'Show'
    
    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'))
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'))
    start_time = db.Column(db.DateTime, nullable=False)
    
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
    venue_data = Venue.query.order_by(Venue.id.desc()).limit(5).all()
    venues = [i.venue_dict() for i in venue_data]
    artist_data = Artist.query.order_by(Artist.id.desc()).limit(5).all()
    artists = [i.artist_dict() for i in artist_data]
    return render_template('pages/home.html', venues=venues, artists=artists)


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    data = [{"city":i.city, 
             "state":i.state
             } for i in Venue.query.distinct('city', 'state').order_by('state', 'city').all()]
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
    form = VenueForm()
    genre_choices = Genre.query.order_by('id').all()
    form.genres.choices = [(i.id, i.name) for i in genre_choices]
    return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    form = VenueForm(request.form)
    genre_choices = Genre.query.order_by('id').all()
    form.genres.choices = [(i.id, i.name) for i in genre_choices]
    error = False   
    if form.validate_on_submit():
        try:
            genre_data = Genre.query.filter(Genre.id.in_(form.genres.data)).order_by('id').all()
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
            flash('An error occurred. Venue ' + form.name.data + ' could not be listed.')
            return render_template('forms/new_venue.html', form=form)
        else:
            # on successful db insert, flash success
            flash('Venue ' + request.form['name'] + ' was successfully listed!')
            return render_template('pages/home.html')
    else:
        flash('An error occurred. Venue ' + form.name.data + ' could not be listed.')
        return render_template('forms/new_venue.html', form=form)
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
      

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    try:
        venue = db.session.query(Venue).get(venue_id)
        db.session.delete(venue)
        db.session.commit()
        result = {'success': True}
    except:
        db.session.rollback()
        result = {'success': False}
    finally:
        db.session.close()
    return jsonify(result)

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
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
  # shows the venue page with the given venue_id
  artist_data = Artist.query.get(artist_id)
  data = artist_data.artist_dict()
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    genre_choices = Genre.query.order_by('id').all()
    form.genres.choices = [(i.id, i.name) for i in genre_choices]
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
    form = ArtistForm(request.form)
    genre_choices = Genre.query.order_by('id').all()
    form.genres.choices = [(i.id, i.name) for i in genre_choices]
    artist = Artist.query.get(artist_id)
    error = False 
    if form.validate_on_submit():
        try:
            genre_data = Genre.query.filter(Genre.id.in_(form.genres.data)).order_by('id').all()
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
            db.session.flush()
            db.session.commit()
        except:
            db.session.rollback()
            error = True
        finally:
            db.session.close()
        if error:
            flash('An error occurred. Artist ' + form.name.data + ' could not be edited.')
            return render_template('forms/edit_artist.html', form=form, artist=artist)
        else:
            return redirect(url_for('show_artist', artist_id=artist_id))
    else:
        return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    genre_choices = Genre.query.order_by('id').all()
    form.genres.choices = [(i.id, i.name) for i in genre_choices]
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
    form = VenueForm(request.form)
    genre_choices = Genre.query.order_by('id').all()
    form.genres.choices = [(i.id, i.name) for i in genre_choices]
    venue = Venue.query.get(venue_id)
    error = False 
    if form.validate_on_submit():
        try:
            genre_data = Genre.query.filter(Genre.id.in_(form.genres.data)).order_by('id').all()
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
            db.session.flush()
            db.session.commit()
        except:
            db.session.rollback()
            error = True
        finally:
            db.session.close()
        if error:
            flash('An error occurred. Venue ' + form.name.data + ' could not be edited.')
            return render_template('forms/edit_venue.html', form=form, venue=venue)
        else:
            return redirect(url_for('show_venue', venue_id=venue_id))
    else:
        return render_template('forms/edit_venue.html', form=form, venue=venue)

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    genre_choices = Genre.query.order_by('id').all()
    form.genres.choices = [(i.id, i.name) for i in genre_choices]
    return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    form = ArtistForm(request.form)
    genre_choices = Genre.query.order_by('id').all()
    form.genres.choices = [(i.id, i.name) for i in genre_choices]
    error = False   
    if form.validate_on_submit():
        try:
            genre_data = Genre.query.filter(Genre.id.in_(form.genres.data)).order_by('id').all()
            artist = Artist(name = form.name.data,
                          city = form.city.data,
                          state = form.state.data,
                          phone = form.phone.data,
                          image_link = form.image_link.data,
                          facebook_link = form.facebook_link.data,
                          genres = genre_data,
                          website = form.website.data,
                          seeking_venue = form.seeking_talent.data,
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
            flash('An error occurred. Artist ' + form.name.data + ' could not be listed.')
            return render_template('forms/new_artist.html', form=form)
        else:
            # on successful db insert, flash success
            flash('Artist ' + request.form['name'] + ' was successfully listed!')
            return render_template('pages/home.html')
    else:
        flash('An error occurred. Artist ' + form.name.data + ' could not be listed.')
        return render_template('forms/new_artist.html', form=form)    

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
    form = ShowForm(request.form)
    error = False   
    if form.validate_on_submit():
        try:
            show = Show(venue_id = form.venue_id.data,
                        artist_id = form.artist_id.data,
                        start_time = form.start_time.data
                        )
            db.session.add(show)
            db.session.commit()
        except:
            db.session.rollback()
            error = True
        finally:
            db.session.close()
        if error:
            flash('An error occurred. Show could not be listed.')
            return render_template('forms/new_show.html', form=form)
        else:
            # on successful db insert, flash success
            flash('Show was successfully listed!')
            return render_template('pages/home.html')
    else:
        flash('An error occurred. Show could not be listed.')
        return render_template('forms/new_show.html', form=form)   

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

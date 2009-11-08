import logging
import os
import urlparse
import datetime
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext import db

class PlaylistTrack(db.Model):
  artist = db.StringProperty(required=True)
  track = db.StringProperty(required=True)
  index = db.IntegerProperty(required=True)
  playlist = db.StringProperty(required=True)
  create_date = db.DateTimeProperty(required=True)

class PlaylistHeader(db.Model):
  title = db.StringProperty(required=True)
  url= db.StringProperty(required=True)
  playlist = db.StringProperty(required=True)
  songs = db.StringProperty(required=True)
  create_date = db.DateTimeProperty(required=True)

class IndexHandler(webapp.RequestHandler):

  def get(self):
    heads = PlaylistHeader.gql("order by create_date desc limit 25");
    template_values = {
        'headers': heads,
        }
    path = os.path.join(os.path.dirname(__file__), 'html/index.html')
    self.response.out.write(template.render(path, template_values))


class PlaylistHeaderHandler(webapp.RequestHandler):

  def get(self):
    playlist_header= PlaylistHeader(title = self.request.get('title'),
                                   url = self.request.get('url'),
                                   songs = self.request.get('songs'),
                                   playlist = self.request.get('playlist'),
                                   create_date = datetime.datetime.now())

    playlist_header.put()
    # logging.error("playlist_header --> %s", playlist_header.title)
    self.response.out.write('broadcast_index++; broadcast_songs();')

class PlaylistTrackHandler(webapp.RequestHandler):

  def get(self):
    playlist_track = PlaylistTrack(artist = self.request.get('artist'),
                                   track = self.request.get('track'),
                                   index = int(self.request.get('index')),
                                   playlist = self.request.get('playlist'),
                                   create_date = datetime.datetime.now())

    playlist_track.put()
    # logging.error("playlist_track --> %s", playlist_track.artist)
    self.response.out.write('broadcast_index++; broadcast_songs();')

class XSPFHandler(webapp.RequestHandler):

  def get(self):
    playlist_key = self.request.path.rstrip('.xspf')
    playlist_key = playlist_key.lstrip('/')

    # logging.error("XSPF key --> %s", playlist_key)

    q = PlaylistHeader.all()
    q.filter('playlist =',playlist_key)
    head = q.fetch(1)[0]
    # logging.error("head -> %s",head.title)

    q = PlaylistTrack.all()
    q.filter('playlist =',playlist_key)
    q.order('index')
    songs = q.fetch(200)
    # for r in songs:
        # logging.error("index -> %s", r.index)
        # logging.error("artist -> %s", r.artist)
        # logging.error("track -> %s", r.track)

    template_values = {
        'header': head,
        'songs': songs,
        }

    path = os.path.join(os.path.dirname(__file__), 'html/xspf-template.xspf')
    self.response.headers['Content-Type'] = 'application/xspf+xml'
    self.response.out.write(template.render(path, template_values))

class ScrapeHandler(webapp.RequestHandler):

  def get(self):
    url = self.request.get('url')
    domain = urlparse.urlparse(url).netloc.lstrip('www.')
    scraper_path = os.path.join(os.path.dirname(__file__), 'scrapers/'+domain+'.js')
    logging.error("scraper_path -> %s",scraper_path)

    if os.path.exists(scraper_path):
        self.response.headers['Content-Type'] = 'text/javascript'
        self.response.out.write(template.render(scraper_path, {}))

def main():
  application = webapp.WSGIApplication([('/scraper.js', ScrapeHandler),
                                       ('/playlist_header.js', PlaylistHeaderHandler),
                                       ('/playlist_track.js', PlaylistTrackHandler),
                                       ('/', IndexHandler),('/.*\.xspf', XSPFHandler)],
                                       debug=True)
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()

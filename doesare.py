#Tornado web server for Does Are
#Programmed by Johann Diedrick
#http://johanndiedrick.com

#To do:
#-simple css design
#-move mongodb and amazon s3 credentials to secure file
#-get background images
#-set up auth for back-end editing pages
#-make a page to delete artists




#import necessary libraries
import os.path
import tornado.httpserver
import tornado.auth
import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web
from tornado.options import define, options
import pymongo
from pymongo import ASCENDING, DESCENDING
from bson.objectid import ObjectId
import boto
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from StringIO import StringIO
import random
import string

#define global port
define("port", default=8000, help="run on the given port", type=int)

#set up handlers for routes
class Application(tornado.web.Application):
	def __init__(self):
		handlers = [
				(r"/", MainHandler),
				(r"/news", NewsHandler),
				(r"/news/edit", NewsEditHandler),
				(r"/about", AboutHandler),
				(r"/about/edit", AboutEditHandler),
				(r"/artists", ArtistsHandler),
				(r"/edit/(\w+)", BandEditHandler),
				(r"/deleteartist/(\w+)", DeleteArtistHandler),
				(r"/add", BandEditHandler),
				(r"/artists/(\w+)", ArtistPageHandler),
				(r"/shop", ShopHandler),
				(r"/shop/edit", ShopEditHandler),
				(r"/contact", ContactHandler),
				(r"/contact/edit", ContactEditHandler),
				(r"/friends", FriendsHandler),
				("/friends/edit", FriendsEditHandler),
				(r"/info", InfoHandler),
				(r"/info/edit", InfoEditHandler),
				(r"/imageupload/(\w+)", ImageUploadHandler),
				(r"/imageuploaded/(\w+)", ImageUploadHandler),
				(r"/shows", ShowsHandler),
				(r"/addshow", ShowEditHandler),
				(r"/show/(\w+)", ShowPageHandler),
				(r"/editshow/(\w+)", ShowEditHandler),
				(r"/deleteshow/(\w+)", DeleteShowHandler),
				(r"/discography", ReleasesHandler),
				(r"/release/(\w+)", ReleasePageHandler),
				(r"/addrelease", ReleaseEditHandler),
				(r"/editrelease/(\w+)", ReleaseEditHandler),
				(r"/deleterelease/(\w+)", DeleteReleaseHandler),
				(r"/releaseimageupload/(\w+)", ReleaseImageUploadHandler),
				(r"/releaseimageuploaded/(\w+)", ReleaseImageUploadHandler)
				]

		settings = dict(
				template_path = os.path.join(os.path.dirname(__file__), "templates"),
				static_path = os.path.join(os.path.dirname(__file__), "static"),
				ui_modules={"Artist": ArtistModule, "Show": ShowModule, "Release": ReleaseModule},
				debug = True,
		)
#mongo db configuration
		conn = pymongo.Connection("mongodb://jdiedrick:Skyl1ne8*@flame.mongohq.com:27078/doesare")
		self.db = conn["doesare"]
		tornado.web.Application.__init__(self, handlers, **settings)

#main handler, renders news page
class MainHandler(tornado.web.RequestHandler):
	def get(self):
		self.redirect("/news")

#news handler, pulls news from mongodb, renders news page
class NewsHandler (tornado.web.RequestHandler):
	def get(self):
		news_content = dict()
		coll = self.application.db.news
		news_content = coll.find_one({"name": "news"})
		self.render(
				"news.html",
				page_title = "Does Are | News",
				header_text = "News",
				news_content = news_content
		)

#news edit handler, pulls news from mongodb for editing, and puts new news into mongodb
class NewsEditHandler(tornado.web.RequestHandler):
	def get(self):
		news_content = dict()
		coll = self.application.db.news
		news_content = coll.find_one({"name": "news"})
		self.render(
				"news_edit.html",
				page_title = "Does Are | Edit the News Page",
				header_text = "Edit the News Page",
				news_content = news_content
		)
	
	def post(self):
		news_field = ['text']
		coll = self.application.db.news
		news_content = dict()
		news_content = coll.find_one({"name": "news"})
		for key in news_field:
			news_content[key] = self.get_argument(key, None)

		coll.save(news_content)
		self.redirect("/news")

#about handler, gets about text from mongodb, renders about page
class AboutHandler(tornado.web.RequestHandler):
	def get(self):
		about_content = dict()
		coll = self.application.db.about
		about_content = coll.find_one({"name": "about"})
		self.render(
				"about.html",
				page_title = "Does Are | About",
				header_text = "About",
				about_content = about_content
		)

#about edit handler, pulls about text from mongodb for editing, and puts new about text into mongodb
class AboutEditHandler(tornado.web.RequestHandler):
	def get(self):
		about_content = dict()
		coll = self.application.db.about
		about_content = coll.find_one({"name": "about"})
		self.render(
				"about_edit.html",
				page_title = "Does Are | Edit the About Page",
				header_text = "Edit the About Page",
				about_content = about_content		
		)

	def post(self):
		about_field = ['text']
		coll = self.application.db.about
		about_content = dict()
		about_content = coll.find_one({"name": "about"})
		for key in about_field:
			about_content[key] = self.get_argument(key, None)

		coll.save(about_content)
		self.redirect("/about")

#artist handler, gets artists from mongodb and renders artists page
class ArtistsHandler(tornado.web.RequestHandler):
	def get(self):
		coll=self.application.db.artists
		artists = coll.find({"active": "true"}).sort("priority", ASCENDING)
		self.render(
				"artists.html",
				page_title = "Does Are | Recommended Artists",
				header_text = "Recommended Artists",
				artists = artists
		)
	
#band edit handler, pulls text from individual artist page from mongo db for editing
class BandEditHandler(tornado.web.RequestHandler):
	def get(self, shortname=None):
		artist = dict()
		if shortname:
			coll = self.application.db.artists
			artist = coll.find_one({"shortname": shortname})
		self.render("artist_edit.html",
				page_title="Does Are | Band",
				header_text = "Edit band",
				artist=artist)

#post handler for editing artists, adds if new or edits if already in database, sends to imageupload handler to upload an image to amazon s3
	def post(self, shortname=None):
		artist_fields = ['fullname', 'shortname', 'members', 'image', 'location', 'description','link', 'releases', 'tourdates', 'contactinfo', 'videos', 'pastshows', 'priority', 'active']
		coll = self.application.db.artists
		artist = dict()
		if shortname:
			artist = coll.find_one({"shortname": shortname})
		for key in artist_fields:
			artist[key] = self.get_argument(key, None)
		
		if shortname:
			coll.save(artist)
		else:
			coll.insert(artist)
		shortname = artist.get('shortname', '') 
		imageroute = "/imageupload/"
		finalroute = imageroute+shortname
		self.redirect(finalroute)

#delete artst handle, removes artist from database
class DeleteArtistHandler(tornado.web.RequestHandler):
	def get(self, name=None):

		self.render("deleteconfirm.html", 
				name = name)
	def post(self, name=None):
		coll = self.application.db.artists
		artist = dict()
		if name:
			artist = coll.find_one({"shortname": name})
			coll.remove(artist)
		self.write("deleted " + name)

#render individual band pages
class ArtistPageHandler(tornado.web.RequestHandler):
	def get(self, name=None):
		artist = dict()
		#return artist from artist database
		if name:
			coll = self.application.db.artists
			artist = coll.find_one({"shortname": name})
		#return releases from artist in database
			coll = self.application.db.releases
			releases = coll.find({"artist": name}).sort("date", ASCENDING)

		self.render("artist_page.html",
				page_title="Does Are | Band Page",
				header_text = "Band Page",
				artist=artist,
				releases=releases)

#module for individual artist
class ArtistModule(tornado.web.UIModule):
	def render(self, artist):
		return self.render_string(
				"modules/artist.html",
				artist=artist,
		)
	
	def css_files(self):
		return "/static/css/recommended.css"

	def javascript_files(self):
		return "/static/js/recommended.js"

#shop handler, gets shop text from db, renders shop page
class ShopHandler(tornado.web.RequestHandler):
	def get(self):
		shop_content = dict()
		coll = self.application.db.shop
		shop_content = coll.find_one({"name": "shop"})

		self.render("shop.html",
				page_title = "Does Are | Shop",
				header_text = "Shop",
				shop_content = shop_content
		)

#shop edit handler, gets shop text from db to edit, updates db with new shop text
class ShopEditHandler(tornado.web.RequestHandler):
	def get(self):
		shop_content = dict()
		coll = self.application.db.shop
		shop_content = coll.find_one({"name": "shop"})
		self.render(
				"shop_edit.html",
				page_title = "Does Are | Edit the Shop Page",
				header_text = "Edit the Shop Page",
				shop_content = shop_content		
		)

	def post(self):
		shop_field = ['text']
		coll = self.application.db.shop
		shop_content = dict()
		shop_content = coll.find_one({"name": "shop"})
		for key in shop_field:
			shop_content[key] = self.get_argument(key, None)

		coll.save(shop_content)
		self.redirect("/shop")

#contact handler, gets contact text from db, renders contact page
class ContactHandler(tornado.web.RequestHandler):
	def get(self):
		contact_content = dict()
		coll = self.application.db.contact
		contact_content = coll.find_one({"name": "contact"})
		self.render("contact.html",
				page_title = "Does Are | Contact",
				header_text = "Contact",
				contact_content = contact_content
		)

#contact edit handler, gets contact text from db, updates db with new contact text
class ContactEditHandler(tornado.web.RequestHandler):
	def get(self):
		contact_content = dict()
		coll = self.application.db.contact
		contact_content = coll.find_one({"name": "contact"})
		self.render(
				"contact_edit.html",
				page_title = "Does Are | Edit the Contact Page",
				header_text = "Edit the Contact Page",
				contact_content = contact_content		
		)

	def post(self):
		contact_field = ['text']
		coll = self.application.db.contact
		contact_content = dict()
		contact_content = coll.find_one({"name": "contact"})
		for key in contact_field:
			contact_content[key] = self.get_argument(key, None)

		coll.save(contact_content)
		self.redirect("/contact")

#friends handler, gets friends text from db, renders friends page
class FriendsHandler(tornado.web.RequestHandler):
	def get(self):
		friends_content = dict()
		coll = self.application.db.friends
		friends_content = coll.find_one({"name": "friends"})

		self.render("friends.html",
				page_title = "Does Are | Friends",
				header_text = "Friends",
				friends_content = friends_content
		)

class InfoHandler(tornado.web.RequestHandler):
	def get(self):
		info_content = dict()
		coll = self.application.db.info
		info_content = coll.find_one({"name": "info"})
		
		self.render("info.html",
				page_title = "Does Are | Info",
				header_text = "Info",
				info_content = info_content
				)

class InfoEditHandler(tornado.web.RequestHandler):
	def get(self):
		info_content = dict()
		coll = self.application.db.info
		info_content = coll.find_one({"name": "info"})
		self.render(
				"info_edit.html",
				page_title = "Does Are | Edit the Info Page",
				header_text = "Edit the Info Page",
				info_content = info_content		
		)

	def post(self):
		info_field = ['text']
		coll = self.application.db.info
		info_content = dict()
		info_content = coll.find_one({"name": "info"})
		for key in info_field:
			info_content[key] = self.get_argument(key, None)

		coll.save(info_content)
		self.redirect("/info")

#friends edit handler, gets friends text from db, updates db with new friends text
class FriendsEditHandler(tornado.web.RequestHandler):
	def get(self):
		friends_content = dict()
		coll = self.application.db.friends
		friends_content = coll.find_one({"name": "friends"})
		self.render(
				"friends_edit.html",
				page_title = "Does Are | Edit the Friends Page",
				header_text = "Edit the Friends Page",
				friends_content = friends_content		
		)

	def post(self):
		friends_field = ['text']
		coll = self.application.db.friends
		friends_content = dict()
		friends_content = coll.find_one({"name": "friends"})
		for key in friends_field:
			friends_content[key] = self.get_argument(key, None)

		coll.save(friends_content)
		self.redirect("/friends")

#image upload handler, renders upload form for particular artist, uploads an image for that artist to amazon s3 and saves location in db for that artist
class ImageUploadHandler(tornado.web.RequestHandler):
	def get(self, shortname=None):
		self.render("imageupload.html", shortname=shortname)

	def post(self, shortname=None):
		artist = dict() #empty dict for artist
		coll = self.application.db.artists # collection of artists
		image=self.request.files['image'][0] #image post data from form
		imagebody=image['body'] #body of image file
		imagename = image['filename'] #image name and path
		conn = S3Connection('AKIAISN6VWLSWH3KLXZQ','93Yb2QSv0mRelZNizM1nvk3tI/7Fq1vmarDQfa9W') #amazon s3 connection
		bucket = conn.create_bucket('doesare_images') #bucket for images
		k = Key(bucket) #key associated with image
		k.key = imagename #sets key to image name
		k.set_metadata("Content-Type", "image/jpeg") #sets metadata for image/jpeg
		k.set_contents_from_string(imagebody) #puts image data into s3 bucket
		k.set_acl('public-read') #makes image public 
		artist = coll.find_one({"shortname": shortname}) #sets artists dict to artist from previous page, which we know is in the database
		artist['image'] = imagename #sets imagename for artist to name of image uploaded
		coll.save(artist) #saves artist info back into database
		self.redirect("/artists") #gives us a confirmation page

class ShowsHandler(tornado.web.RequestHandler):
	def get(self):
		allartists=self.application.db.artists
		coll=self.application.db.shows
		individual_artists=set()
		artistsshows = dict()
		finalHTML = ""
		fullname=""
		for show in coll.find():
			individual_artists.add(show['artist'])


		for artist in individual_artists:
			#find full name
			#artistindb=""
			artistindb = allartists.find_one({"shortname": artist})
			finalHTML = finalHTML + "<b>"
			finalHTML = finalHTML + artistindb['fullname']
			finalHTML = finalHTML + "</b>"
			finalHTML = finalHTML + "<br>"
			for artistshow in coll.find({"artist": artist}).sort("date", ASCENDING):
				finalHTML = finalHTML + artistshow['date']
				finalHTML = finalHTML + " | "
				finalHTML = finalHTML + artistshow['location']
				finalHTML = finalHTML + " | "
				finalHTML = finalHTML + artistshow['venue']
				finalHTML = finalHTML + " | "
				finalHTML = finalHTML + artistshow['time']
				finalHTML = finalHTML + " | "
				finalHTML = finalHTML + "<a href=/show/"
				finalHTML = finalHTML + str(artistshow['_id']) 
				finalHTML = finalHTML + ">More details</a>"
				finalHTML = finalHTML + "<br>"
			finalHTML = finalHTML+"<br>"
		
		self.render(
				"shows_new.html",
				page_title = "Does Are | Shows",
				header_text = "Shows",
				finalHTML = finalHTML
				)
			

#class ShowsHandler(tornado.web.RequestHandler):
#	def get(self):
#		coll=self.application.db.shows
#		shows = coll.find().sort("date", ASCENDING)
#		
#		
#		self.render(
#				"shows.html",
#				page_title = "Does Are | Shows",
#				header_text = "Shows",
#				shows = shows
#		)

	
	
#show edit handler, allows for adding a new show  or editing an upcoming one
class ShowEditHandler(tornado.web.RequestHandler):
	def get(self, showid=None):
		allartists=dict()
		show = dict()


		if showid:
			coll = self.application.db.shows
			show = coll.find_one({"_id": ObjectId(showid)})
		coll=self.application.db.artists
		allartists = coll.find()
		self.render("show_edit.html",
				page_title="Does Are | Show",
				header_text = "Edit show",
				show=show,
				allartists=allartists
				)

#post handler for editing shows, adds if new or edits if already in database, sends to imageupload handler to upload an image to amazon s3
	def post(self, showid=None):
		show_fields = ['artist', 'date', 'venue', 'location', 'time', 'address','playingwith', 'description', 'sharelinks']
		coll = self.application.db.shows
		show = dict()
		if showid:
			show = coll.find_one({"_id": ObjectId(showid)})
		for key in show_fields:
			show[key] = self.get_argument(key, None)
		
		if showid:
			coll.save(show)
		else:
			coll.insert(show)
		self.redirect("/shows")


#render individual band pages
class ShowPageHandler(tornado.web.RequestHandler):
	def get(self, showid=None):
		show = dict()
		artist = dict()
		artistsindb = self.application.db.artists
		
		if showid:
			coll = self.application.db.shows
			show = coll.find_one({"_id": ObjectId(showid)})
		
		shortname = show['artist']
		artistfullname = artistsindb.find_one({"shortname": shortname})['fullname']
		self.render("show_page.html",
				page_title="Does Are | Band Page",
				header_text = "Show Page",
				show=show,
				artistfullname = artistfullname
				)


#delete show handle, removes show from database
class DeleteShowHandler(tornado.web.RequestHandler):
	def get(self, showid=None):

		self.render("deleteshowconfirm.html", 
				showid = showid)
	def post(self, showid=None):
		coll = self.application.db.shows
		show = dict()
		if showid:
			show = coll.find_one({"_id": ObjectId(showid)})
			coll.remove(show)
		self.redirect("/shows")
#module for individual show
class ShowModule(tornado.web.UIModule):
	def render(self, show):
		return self.render_string(
				"modules/show.html",
				show=show,
		)
	
	def css_files(self):
		return "/static/css/recommended.css"

	def javascript_files(self):
		return "/static/js/recommended.js"


class ReleasesHandler(tornado.web.RequestHandler):
	def get(self):
		finalHTML = ""
		
		releasescollection=self.application.db.releases
		releases = releasescollection.find().sort("date", ASCENDING)
		
		allartists=self.application.db.artists
		for release in releases:
			releaseartist = release["artist"]
			artistindb = allartists.find_one({"shortname": releaseartist})
			finalHTML = finalHTML + "<p>"
			finalHTML = finalHTML + release['catnum']
			finalHTML = finalHTML + " | "
			finalHTML = finalHTML + "<a href=/release/"
			finalHTML = finalHTML + str(release['_id'])
			finalHTML = finalHTML + '>'
			finalHTML = finalHTML + release['title']
			finalHTML = finalHTML + "</a>"
			finalHTML = finalHTML + " by "
			finalHTML = finalHTML + artistindb['fullname']
			finalHTML = finalHTML + "</p>"


		self.render(
				"releases.html",
				page_title = "Does Are | Releases",
				header_text = "Releases",
				finalHTML = finalHTML
		)

#render individual releases
class ReleasePageHandler(tornado.web.RequestHandler):
	def get(self, releaseid=None):
		release = dict()
		artist = dict()
		artistsindb = self.application.db.artists
		
		if releaseid:
			coll = self.application.db.releases
			release = coll.find_one({"_id": ObjectId(releaseid)})
		
		shortname = release['artist']
		artistfullname = artistsindb.find_one({"shortname": shortname})['fullname']
		self.render("release_page.html",
				page_title="Does Are | Release Page",
				header_text = "Release Page",
				release=release,
				artistfullname = artistfullname
				)


class ReleaseEditHandler(tornado.web.RequestHandler):
	def get(self, releaseid=None):
		release = dict()
		allartists = dict()

		if releaseid:
			coll = self.application.db.releases
			release = coll.find_one({"_id": ObjectId(releaseid)})
		coll = self.application.db.artists
		allartists = coll.find()
		self.render("release_edit.html",
				page_title="Does Are | Discography",
				header_text = "Edit release",
				release=release,
				allartists=allartists
				)

#post handler for editing artists, adds if new or edits if already in database, sends to imageupload handler to upload an image to amazon s3
	def post(self, releaseid=None):
		release_fields = ['artist', 'title', 'date', 'catnum', 'image', 'description']
		coll = self.application.db.releases
		release = dict()
		if releaseid:
			release = coll.find_one({"_id": ObjectId(releaseid)})
		for key in release_fields:
			release[key] = self.get_argument(key, None)
		
		if releaseid:
			coll.save(release)
		else:
			coll.insert(release)
		releaseid=release.get("_id", "")
		releaseid = str(releaseid) #change objectid to string
		imageroute = "/releaseimageupload/"
		finalroute = imageroute + releaseid
		self.redirect(finalroute)


#image upload handler, renders upload form for particular artist, uploads an image for that artist to amazon s3 and saves location in db for that artist
class ReleaseImageUploadHandler(tornado.web.RequestHandler):
	def get(self, releaseid=None):
		self.render("releasesimageupload.html", releaseid=releaseid)

	def post(self, releaseid=None):
		release = dict() #empty dict for artist
		coll = self.application.db.releases # collection of artists
		release = coll.find_one({"_id": ObjectId("50f1c86988ea0f4fa2376f5f")})
		image=self.request.files['image'][0] #image post data from form
		imagebody=image['body'] #body of image file
		imagename = image['filename'] #image name and path
		conn = S3Connection('AKIAISN6VWLSWH3KLXZQ','93Yb2QSv0mRelZNizM1nvk3tI/7Fq1vmarDQfa9W') #amazon s3 connection
		bucket = conn.create_bucket('doesare_images') #bucket for images
		k = Key(bucket) #key associated with image
		k.key = imagename #sets key to image name
		k.set_metadata("Content-Type", "image/jpeg") #sets metadata for image/jpeg
		k.set_contents_from_string(imagebody) #puts image data into s3 bucket
		k.set_acl('public-read') #makes image public 
		release = coll.find_one({"_id": ObjectId(releaseid)}) #sets artists dict to artist from previous page, which we know is in the database
		#print(releaseid)
		release['image'] = imagename #sets imagename for artist to name of image uploaded
		coll.save(release) #saves artist info back into database
		#self.write(release)
		self.redirect("/discography") #gives us a confirmation page

#delete show handle, removes show from database
class DeleteReleaseHandler(tornado.web.RequestHandler):
	def get(self, releaseid=None):

		self.render("deletereleaseconfirm.html", 
				releaseid = releaseid)
	def post(self, releaseid=None):
		coll = self.application.db.releases
		release = dict()
		if releaseid:
			release = coll.find_one({"_id": ObjectId(releaseid)})
			coll.remove(release)
		self.redirect("/discography")

#module for individual release
class ReleaseModule(tornado.web.UIModule):
	def render(self, release):
		return self.render_string(
				"modules/release.html",
				release=release,
		)
	
	def css_files(self):
		return "/static/css/recommended.css"

	def javascript_files(self):
		return "/static/js/recommended.js"


#boilerplate for starting server
if __name__ == "__main__":
	tornado.options.parse_command_line()
	http_server = tornado.httpserver.HTTPServer(Application())
	http_server.listen(options.port)
	tornado.ioloop.IOLoop.instance().start()

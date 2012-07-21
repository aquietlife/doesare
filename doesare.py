import os.path
import tornado.httpserver
import tornado.auth
import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web
from tornado.options import define, options
import pymongo

define("port", default=8000, help="run on the given port", type=int)

class Application(tornado.web.Application):
	def __init__(self):
		handlers = [
				(r"/", MainHandler),
				(r"/recommended/", RecommendedHandler),
				(r"/edit/(\w+)", BandEditHandler),
				(r"/add", BandEditHandler)
		]

		settings = dict(
				template_path = os.path.join(os.path.dirname(__file__), "templates"),
				static_path = os.path.join(os.path.dirname(__file__), "static"),
				ui_modules={"Band": BandModule},
				debug = True,
		)

		conn = pymongo.Connection("localhost", 27017)
		self.db = conn["bands"]
		tornado.web.Application.__init__(self, handlers, **settings)

class MainHandler(tornado.web.RequestHandler):
	def get(self):
		self.render(	
				"index.html",
				page_title = "Does Are | It's a Label",
				header_text = "Does Are Label Site",
		)

class RecommendedHandler(tornado.web.RequestHandler):
	def get(self):
		coll=self.application.db.band
		bands = coll.find()
		self.render(
				"recommended.html",
				page_title = "Does Are | Recommended Artists",
				header_text = "Recommended Artists",
				bands = bands
		)

class BandEditHandler(tornado.web.RequestHandler):
	def get(self, name=None):
		band = dict()
		if name:
			coll = self.application.db.band
			band = coll.find_one({"name": name})
		self.render("book_edit.html",
				page_title="Does Are | Band",
				header_text = "Edit band",
				band=band)
	
	def post(self, name=None):
		band_fields = ['name', 'image', 'description', 'releases', 'tourdates', 'contactinfo']
		coll = self.application.db.band
		band = dict()
		if name:
			band = coll.find_one({"name": name})
		for key in band_fields:
			band[key] = self.get_argument(key, None)

		if name:
			coll.save(band)
		else:
			coll.insert(band)
		self.redirect("/recommended/")

class BandModule(tornado.web.UIModule):
	def render(self, band):
		return self.render_string(
				"modules/band.html",
				band=band,
		)
	
	def css_files(self):
		return "/static/css/recommended.css"

	def javascript_files(self):
		return "/static/js/recommended.js"

if __name__ == "__main__":
	tornado.options.parse_command_line()
	http_server = tornado.httpserver.HTTPServer(Application())
	http_server.listen(options.port)
	tornado.ioloop.IOLoop.instance().start()

#!/usr/bin/python

import sys, os, logging, ConfigParser, getopt
from lxml import etree

logging.basicConfig(level=logging.INFO)

class Pipeline:
	def __init__(self, base_dir, test_collection, test_name):
		self.base_dir = base_dir
		self.test_collection = test_collection
		self.test_name = test_name

		self.doc_path = os.path.join(self.base_dir, "static", "tests", self.test_collection, "src", "docx", "")
		self.doc_fn = self.doc_path+self.test_name+".docx"

		self.xml_path = os.path.join(self.base_dir, "static", "tests", self.test_collection, "src", "xml", self.test_name)
		self.xml_fn = self.xml_path+".xml"

		self.fo_fn = os.path.join(self.base_dir, "static", "tests", self.test_collection, "src", "fo", self.test_name+".fo")
		self.html_fn = os.path.join(self.base_dir, "static", "tests", self.test_collection, "src", "html", self.test_name+".html")
		
		self.pdf_path = os.path.join(self.base_dir, "static", "tests", self.test_collection, "pdf", "")

	def doc2xml(self):
		logging.info("DOCX -> XML")

		cmd = []
		# Call meTypeset
		cmd.append(" ".join([os.path.join(self.base_dir, "static/tools/meTypeset/bin/meTypeset.py"), "docx", self.doc_fn, self.xml_path]))
		# Move output to XML dir
		cmd.append(" ".join(["mv", os.path.join(self.xml_path, "nlm", "out.xml"), self.xml_fn]))
		# Clean output dir
		cmd.append(" ".join(["rm", "-r", self.xml_path]))
		
		# Execute commands
		for c in cmd:
			logging.info(c)
			os.system(c)

		logging.info("... done")

	def xml2fo(self, xsl_fn):
		logging.info("XML -> FO")

		# Load stylesheet
		xsl = etree.parse(xsl_fn)
		transformer = etree.XSLT(xsl)
		
		# Transform XML
		xml = etree.parse(self.xml_fn)
		fo = transformer(xml)

		logging.info("... done")

		# Save FO
		logging.info("Writing to %s"%self.fo_fn)
		fo.write(self.fo_fn, encoding="utf-8")

	def xml2html(self, xsl_fn):
		logging.info("XML -> HTML")

		# Load stylesheet
		xsl = etree.parse(xsl_fn)
		transformer = etree.XSLT(xsl)
		
		# Transform XML
		xml = etree.parse(self.xml_fn)
		html = transformer(xml)

		logging.info("... done")

		# Save HTML
		logging.info("Writing to %s"%self.html_fn)
		html.write(self.html_fn, encoding="utf-8")
		
 	def pdf(self, tool, path, css_fn):
 		out = self.pdf_path + self.test_name + "." + tool + ".pdf"
 		
 		if tool == "mpdf":
 			cmd = " ".join(["php", path, "--css", css_fn, "--html", self.html_fn, "-o", self.pdf_path + self.test_name + "." + "mpdf" + ".pdf"])
 		elif tool == "prince":
 			cmd = " ".join([path, self.html_fn, "-s", css_fn, "-o", self.pdf_path + self.test_name + "." + "prince" + ".pdf"])
 		elif tool == "fop":
 			cmd = " ".join([path, self.fo_fn, self.pdf_path + self.test_name + "." + "fop" + ".pdf"])
 		elif tool == "ahf":
 		 	cmd = " ".join([path, "-d", self.fo_fn, "-o", self.pdf_path + self.test_name + "." + "ahf" + ".pdf"])
 		else:
 			sys.stderr.write("Unknown tool %s\n Tool options are 'mpdf', 'prince', 'fop' and 'ahf'.\n"%tool)
 			sys.exit()

		logging.info(cmd)
		os.system(cmd)

def usage():
	sys.stderr.write("./test.py -c config\n")

def main():
	# Process config and command line options
	options, rest = getopt.getopt(sys.argv[1:], "c:", ["config="])

	cfg_fn = ""
	for opt, arg in options:
		if opt in ("-c", "--config"):
			cfg_fn = arg
		else:
			sys.stderr.write("Unknown option %s"%opt)
			exit(1)

	if not cfg_fn:
		usage()
		exit(1)

	if not(os.path.isfile(cfg_fn)):
		sys.stderr.write("File %s not found"%cfg_fn)
		exit(1)

	cfg = ConfigParser.ConfigParser()
	cfg.read(cfg_fn)
	base_dir = cfg.get("general", "base_dir")
	test_collection = cfg.get("general", "test_collection")
	test_name = cfg.get("general", "test_name")
	xslt_html=cfg.get("stylesheets", "xslt_html")
	xslt_fo=cfg.get("stylesheets", "xslt_fo")
	css=cfg.get("stylesheets", "css")
	
	P = Pipeline(base_dir, test_collection, test_name)
	P.doc2xml()

	P.xml2fo(xslt_fo)
	P.xml2html(xslt_html)
	
	for tool, path in cfg.items("tools"):
		P.pdf(tool, path, css)
#	P.mpdf(cfg.get("tools", "mpdf"), css)
#	P.prince(cfg.get("tools", "prince"), css)
#	P.fop(cfg.get("tools", "fop"), css)
#	P.ahf(cfg.get("tools", "ahf"), css)

	

if __name__ == "__main__":
	main()
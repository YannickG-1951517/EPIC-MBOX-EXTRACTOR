__author__ = "Yannick Goedhuys"
__version__ = 1.0
__date__ = "6/9/2022"


import mailbox
import base64
import os
from sre_parse import Verbose
import sys
import email


BLACKLIST = ('signature.asc', 'message-footer.txt', 'smime.p7s')
VERBOSE = 1 # 0 = silent, 1 = verbose, 2 = debug

attachments = 0 #Count extracted attachment
skipped = 0

# Search for filename or find recursively if it's multipart
def extract_attachment(payload):
	global attachments, skipped
	filename = payload.get_filename()

	if filename is not None:
		print("\nAttachment found!")
		if filename.find('=?') != -1:
			ll = email.header.decode_header(filename)
			filename = ""
			for l in ll:
				filename = filename + l[0]
			
		if filename in BLACKLIST:
			skipped = skipped + 1
			if (VERBOSE >= 1):
				print("Skipping %s (blacklist)\n" %filename)
			return

		content = payload.as_string()
		# Skip headers, go to the content
		fh = content.find('\n\n')
		content = content[fh:]

		# if it's base64....
		if payload.get('Content-Transfer-Encoding') == 'base64':
			# content = base64.decodestring(content)
			content = base64.b64decode(content)
		# quoted-printable
		# what else? ...

		if (VERBOSE >= 1):
			print("Extracting %s (%d bytes)\n" %(filename, len(content)))

		n = 1
		orig_filename = filename
		while os.path.exists(filename):
			filename = orig_filename + "." + str(n)
			n = n+1

		try:
			fp = open(filename, "wb")
#			fp = open(str(i) + "_" + filename, "w")
			fp.write(content)
		except IOError:
			print("Aborted, IOError!!!")
			sys.exit(2)
		finally:
			fp.close()	

		attachments = attachments + 1
	else:
		if payload.is_multipart():
			for payl in payload.get_payload():
				extract_attachment(payl)

if (VERBOSE >= 1):
	print("Extract attachments from mbox files")

if len(sys.argv) < 2 or len(sys.argv) > 3:
	print("Usage: %s <mbox_file> [directory]" %sys.argv[0])
	sys.exit(0)

filename = sys.argv[1]
print(filename)
directory = os.path.curdir

if not os.path.exists(filename):
	print("File doesn't exist:", filename)
	sys.exit(1)

if len(sys.argv) == 3:
	directory = sys.argv[2]
	if not os.path.exists(directory) or not os.path.isdir(directory):
		print("Directory doesn't exist:", directory)
		sys.exit(1)

mb = mailbox.mbox(filename)

os.chdir(directory)

for i in range(mb.__len__()):
	if (VERBOSE >= 1):
		print("message %d" %i)
	if (VERBOSE >= 2):
		print("Analyzing message number", i)

	mes = mb.get_message(i)
	# print(mes)
	em = email.message_from_string(mes.as_string())
	print(em)

	subject = em.get('Subject')
	if subject.find('=?') != -1:
		ll = email.header.decode_header(subject)
		subject = ""
		for l in ll:
			subject = subject + l[0].decode()

	em_from = em.get('From')
	if em_from.find('=?') != -1:
		ll = email.header.decode_header(em_from)
		em_from = ""
		for l in ll:
			em_from = em_from + l[0].decode()

	if (VERBOSE >= 2):
		print("%s - From: %s" %(subject, em_from))

	filename = mes.get_filename()
	
	# Puede tener filename siendo multipart???
	if em.is_multipart():
		for payl in em.get_payload():
			extract_attachment(payl)
	else:
		extract_attachment(em)

if (VERBOSE >= 1):
	print("\n--------------")
	print("Total attachments extracted:", attachments)
	print("Total attachments skipped:", skipped)

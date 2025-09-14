from sqlorm import SQLType
from flask_files import save_file, File


File = SQLType("text", save_file, File.from_uri)

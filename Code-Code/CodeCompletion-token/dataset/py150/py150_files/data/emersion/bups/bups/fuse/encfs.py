import os
import subprocess
from base import FuseBase

class FuseEncfs(FuseBase):
	def __init__(self):
		FuseBase.__init__(self)

	def mount(self, mount_path, parent_path=None):
		if parent_path is None:
			raise ValueError("EncFS filesystem requires parent path")

		FuseBase.mount(self, mount_path)

		res = subprocess.call(["encfs --standard --extpass=/usr/lib/ssh/ssh-askpass "+parent_path+" "+mount_path], shell=True)
		if res != 0:
			raise RuntimeError("Cannot mount encfs filesystem [#"+str(res)+"]")

	def get_type(self):
		return "encfs"
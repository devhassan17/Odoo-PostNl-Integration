# postnl_odoo_integration/services/sftp_client.py
import paramiko


class PostNLSFTPClient(object):
    def __init__(self, host, port=22, username=None, password=None):
        self.host = host
        self.port = port or 22
        self.username = username
        self.password = password

    def _get_client(self):
        transport = paramiko.Transport((self.host, self.port))
        transport.connect(username=self.username, password=self.password)
        return paramiko.SFTPClient.from_transport(transport)

    def test_connection(self):
        sftp = self._get_client()
        try:
            sftp.listdir(".")
        finally:
            sftp.close()

    def upload_file(self, remote_dir, filename, content_bytes: bytes):
        sftp = self._get_client()
        try:
            if remote_dir:
                try:
                    sftp.chdir(remote_dir)
                except IOError:
                    sftp.mkdir(remote_dir)
                    sftp.chdir(remote_dir)
            with sftp.open(filename, "wb") as f:
                f.write(content_bytes)
        finally:
            sftp.close()

    def list_files(self, remote_dir):
        sftp = self._get_client()
        try:
            return sftp.listdir(remote_dir)
        finally:
            sftp.close()

    def read_file(self, remote_dir, filename):
        sftp = self._get_client()
        try:
            sftp.chdir(remote_dir)
            with sftp.open(filename, "rb") as f:
                return f.read()
        finally:
            sftp.close()

    def delete_file(self, remote_dir, filename):
        sftp = self._get_client()
        try:
            sftp.chdir(remote_dir)
            sftp.remove(filename)
        finally:
            sftp.close()

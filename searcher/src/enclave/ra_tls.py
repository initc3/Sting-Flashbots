import ctypes
import errno
import os
import select 
import socket
import sys
import ssl
import requests
import warnings
import urllib3
from io import BytesIO, StringIO
import datetime
from OpenSSL import SSL

from requests.adapters import HTTPAdapter, DEFAULT_POOLBLOCK
from requests.packages.urllib3 import PoolManager, HTTPSConnectionPool
from requests.packages.urllib3.poolmanager import _DEFAULT_BLOCKSIZE, SSL_KEYWORDS
from requests.packages.urllib3.connection import HTTPSConnection 
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

HOST = None
PORT = None
CONNECTION = None
SOCKET = None

if os.environ.get("INSIDE_SGX", 0) == "1":
    lib_path = "/lib"
else:
    lib_path = "/usr/src/gramine/build/tools/sgx/ra-tls"

SO_PATH = {
    "epid": f"{lib_path}/libra_tls_verify_epid.so",
    "dcap": f"{lib_path}/libra_tls_verify_dcap.so"
}
VERIFY_LIB = ctypes.CDLL(SO_PATH[os.environ.get("RA_TYPE", "epid")])
CERT_DER = None


def get_ra_tls_session(host, port, cert_der_path):
    context = SSL.Context(SSL.TLSv1_2_METHOD)
    cert_pem_path = os.path.splitext(cert_der_path)[0] + ".pem"
    convert_der_pem(cert_der_path, cert_pem_path)
    context.load_verify_locations(cert_pem_path)
    context.set_options(SSL.OP_NO_SSLv2)
    context.set_verify(SSL.VERIFY_PEER | SSL.VERIFY_FAIL_IF_NO_PEER_CERT, verify_callback)
    global CONNECTION, SOCKET, HOST, PORT, CERT_DER
    CERT_DER = open(cert_der_path, "rb").read()
    HOST = host 
    PORT = port
    SOCKET = socket.socket()
    CONNECTION = MySSLConnection(context, SOCKET)
    CONNECTION.connect((host, port))
    CONNECTION.do_handshake()
    s = requests.Session()
    s.mount('https://', MyAdapter())
    return s

def verify_callback(connection, x509, errnum, depth, ok):
    assert depth == 0  # because this is a self signed certificate
    ra_tls_result = ra_tls_verify_callback_results(0,0,_U(epid(),dcap(),misc()))
    ra_tls_result_p = ctypes.pointer(ra_tls_result)
    ret = VERIFY_LIB.ra_tls_verify_callback_extended_der(CERT_DER, len(CERT_DER), ra_tls_result_p)
    print("ra_tls_verify_callback ret", ret)
    return ret == 0

def convert_der_pem(cert_der_path, cert_pem_path):
    with open(cert_der_path, "rb") as f:
        der = f.read()
    pem = ssl.DER_cert_to_PEM_cert(der)
    with open(cert_pem_path, "w") as f:
        f.write(pem)

#types from https://github.com/gramineproject/gramine/blob/master/tools/sgx/ra-tls/ra_tls.h
class epid(ctypes.Structure):
    _fields_ = [('ias_enclave_quote_status', ctypes.c_char * 128)]

class dcap(ctypes.Structure):
    _fields_ = [('func_verify_quote_result', ctypes.c_int),
                ('quote_verification_result', ctypes.c_int)]

class misc(ctypes.Structure):
    _fields_ = [('reserved', ctypes.c_char * 128)]

class _U(ctypes.Union):
    _fields_ = [("epid", epid),
                ("dcap", dcap),
                ("misc", misc)]
    
class ra_tls_verify_callback_results(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [('ra_tls_attestation_scheme_t', ctypes.c_int),
                ('ra_tls_err_loc_t', ctypes.c_int),
                ('u', _U)]

#adapted from https://stackoverflow.com/questions/14665064/using-python-requests-with-existing-socket-connection
class MyAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=DEFAULT_POOLBLOCK, **pool_kwargs):
        """Initializes a urllib3 PoolManager.

        This method should not be called from user code, and is only
        exposed for use when subclassing the
        :class:`HTTPAdapter <requests.adapters.HTTPAdapter>`.

        :param connections: The number of urllib3 connection pools to cache.
        :param maxsize: The maximum number of connections to save in the pool.
        :param block: Block when no free connections are available.
        :param pool_kwargs: Extra keyword arguments used to initialize the Pool Manager.
        """
        # save these values for pickling
        self._pool_connections = connections
        self._pool_maxsize = maxsize
        self._pool_block = block

        self.poolmanager = MyPoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            **pool_kwargs,
        )

class MyPoolManager(PoolManager):
    def _new_pool(self, scheme, host, port, request_context):
        if request_context is None:
            request_context = self.connection_pool_kw.copy()

        # Default blocksize to _DEFAULT_BLOCKSIZE if missing or explicitly
        # set to 'None' in the request_context.
        if request_context.get("blocksize") is None:
            request_context["blocksize"] = _DEFAULT_BLOCKSIZE

        # Although the context has everything necessary to create the pool,
        # this function has historically only used the scheme, host, and port
        # in the positional args. When an API change is acceptable these can
        # be removed.
        for key in ("scheme", "host", "port"):
            request_context.pop(key, None)

        if scheme == "http":
            for kw in SSL_KEYWORDS:
                request_context.pop(kw, None)
        if scheme == 'https' and host == HOST and port == PORT:
            return MyHTTPSConnectionPool(host, port, **request_context)
        return super(PoolManager, self)._new_pool(self, scheme, host, port, request_context=request_context)      

class MyHTTPSConnectionPool(HTTPSConnectionPool):
    def _new_conn(self):
        """
        Return a fresh :class:`HTTPConnection`.
        """
        self.num_connections += 1
        # log.debug(
        #     f"Starting new HTTP connection ({self.num_connections}): {self.host}:{self.port}",
        # )
        conn = MyHTTPConnection(
            host=self.host,
            port=self.port,
            timeout=self.timeout.connect_timeout,
            **self.conn_kw,
        )
        return conn

class MyHTTPConnection(HTTPSConnection):
    def connect(self) -> None:
        self.sock = sock = CONNECTION
        server_hostname: str = self.host
        tls_in_tls = False

        # Do we need to establish a tunnel?
        if self._tunnel_host is not None:
            # We're tunneling to an HTTPS origin so need to do TLS-in-TLS.
            if self._tunnel_scheme == "https":
                self.sock = sock = self._connect_tls_proxy(self.host, sock)
                tls_in_tls = True

            # If we're tunneling it means we're connected to our proxy.
            self._has_connected_to_proxy = True

            self._tunnel()  # type: ignore[attr-defined]
            # Override the host with the one we're requesting data from.
            server_hostname = self._tunnel_host

        if self.server_hostname is not None:
            server_hostname = self.server_hostname
        RECENT_DATE = datetime.date(2023, 5, 10)
        is_time_off = datetime.date.today() < RECENT_DATE
        if is_time_off:
            warnings.warn(
                (
                    f"System time is way off (before {RECENT_DATE}). This will probably "
                    "lead to SSL verification errors"
                ),
                urllib3.exceptions.SystemTimeWarning.SystemTimeWarning,
            )

        CONNECTION.do_handshake()
        self.is_verified = True

        # If there's a proxy to be connected to we are fully connected.
        # This is set twice (once above and here) due to forwarding proxies
        # not using tunnelling.
        self._has_connected_to_proxy = bool(self.proxy)    

#adapted from https://pythonhosted.org/ndg-httpsclient/ndg.httpsclient.ssl_socket-pysrc.html#SSLSocket.makefile
class MySSLConnection(SSL.Connection):
    def makefile(self, mode="r", buffering=None, *,
                 encoding=None, errors=None, newline=None):
        """Specific to Python socket API and required by httplib: convert 
        response into a file-like object.  This implementation reads using recv 
        and copies the output into a StringIO buffer to simulate a file object 
        for consumption by httplib 

        Nb. Ignoring optional file open mode (StringIO is generic and will 
        open for read and write unless a string is passed to the constructor) 
        and buffer size - httplib set a zero buffer size which results in recv 
        reading nothing 

        @return: file object for data returned from socket 
        @rtype: cStringIO.StringO 
        """ 

        if not hasattr(self, "_makefile_refs"):
            self._makefile_refs = 0
        if not hasattr(self, "buf_size"):
            self.buf_size = 65537
        self._makefile_refs += 1 

        # Optimisation 
        _buf_size = self.buf_size 
        assert("r" in mode)
        i=0 
        if "b" in mode:
            stream = BytesIO() 
        else:
            stream = StringIO() 

        # startTime = datetime.utcnow() 
        try: 
            select.select([SOCKET], [], [])
            dat = self.recv(_buf_size) 
            stream.write(dat) 
        except (SSL.ZeroReturnError, SSL.SysCallError): 
            # Connection is closed - assuming here that all is well and full 
            # response has been received.  httplib will catch an error in 
            # incomplete content since it checks the content-length header 
            # against the actual length of data received 
            pass 

        # if log.getEffectiveLevel() <= logging.DEBUG: 
        #     log.debug("Socket.makefile %d recv calls completed in %s", i, 
        #             datetime.utcnow() - startTime) 

        # Make sure to rewind the buffer otherwise consumers of the content will 
        # read from the end of the buffer 
        stream.seek(0) 

        return stream         


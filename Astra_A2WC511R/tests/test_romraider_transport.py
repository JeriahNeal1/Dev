"""Real loopback HTTP tests for session reuse and uncertain commit failures."""
import concurrent.futures,http.server,json,pathlib,socket,sys,tempfile,threading,unittest
sys.path.insert(0,str(pathlib.Path(__file__).parents[1]/'integrations/romraider_mcp'))
from core import Bridge
class Server(http.server.ThreadingHTTPServer):
    daemon_threads=True
class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version='HTTP/1.1'
    calls=[]
    def log_message(self,*a):pass
    def do_POST(self):
        q=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        self.server.calls.append((q,self.client_address))
        if q['op']=='commit_lost_response':
            self.connection.shutdown(socket.SHUT_RDWR);self.connection.close();self.close_connection=True;return
        if q['op']=='redirect':
            self.send_response(302);self.send_header('Location','http://example.invalid');self.send_header('Content-Length','0');self.end_headers();return
        data=json.dumps({'ok':True,'result':{'op':q['op'],'size':q['args'].get('size','')}}).encode()
        self.send_response(200);self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
class TransportTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=pathlib.Path(self.tmp.name)/'connection.json'
        self.server=Server(('127.0.0.1',0),Handler);self.server.calls=[]
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.path.write_text(json.dumps({'url':f'http://127.0.0.1:{self.server.server_port}/rpc','token':'a'*64}));self.b=Bridge(self.path)
    def tearDown(self):self.b.close();self.server.shutdown();self.server.server_close();self.thread.join();self.tmp.cleanup()
    def test_reuses_one_socket_for_large_snapshots(self):
        for _ in range(12):self.assertEqual(self.b.request('snapshot',{'size':'z'*100000})['size'],'z'*100000)
        self.assertEqual(len(set(c[1] for c in self.server.calls)),1)
    def test_concurrent_callers_serialized(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as p:self.assertEqual(len(list(p.map(lambda i:self.b.request('status',{}),range(12)))),12)
        self.assertEqual(len(set(c[1] for c in self.server.calls)),1)
    def test_lost_commit_response_is_never_retried(self):
        with self.assertRaises(Exception):self.b.request('commit_lost_response',{})
        self.assertEqual(len(self.server.calls),1)
        self.assertEqual(self.b.request('status',{})['op'],'status');self.assertEqual(len(self.server.calls),2)
    def test_redirect_is_rejected_without_following(self):
        with self.assertRaises(RuntimeError):self.b.request('redirect',{})
        self.assertEqual(len(self.server.calls),1)
    def test_changed_connection_identity_gets_new_socket(self):
        self.b.request('status',{});v=json.loads(self.path.read_text());v['token']='b'*64;self.path.write_text(json.dumps(v));self.b.request('status',{})
        self.assertEqual(len(set(c[1] for c in self.server.calls)),2)
    def test_non_loopback_url_refused_before_connection(self):
        self.path.write_text(json.dumps({'url':'http://example.invalid/rpc','token':'a'*64}))
        with self.assertRaises(ValueError):self.b.request('status',{})
        self.assertEqual(self.server.calls,[])
if __name__=='__main__':unittest.main()

from SocketServer import ThreadingMixIn
import Queue
import BaseHTTPServer
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import errno
import getopt
import os
import sys
import urllib2
from os import listdir
from os.path import isfile, join
import thread

cache = {}
mypath = os.getcwd()+'/Cache';

def getFileName(path):
	return path.replace('/','_');
        
class cacheHandler:
    total_directory_size = 50000;
    def __init__(self):
        if not os.path.exists(mypath):
            os.makedirs('Cache')
            
        files = [f for f in listdir(mypath) if isfile(join(mypath,f))]

        for file in files:
            cache[file] = 1;
            cacheHandler.total_directory_size = cacheHandler.total_directory_size + os.stat('Cache/'+file).st_size;
        
    def updateCache(self,fileName,file):

        file_size = sys.getsizeof(file);
        if len(cache) != 0:
            least_frequent_file = min(cache, key=cache.get);
            least_frequent_file_size = os.stat('Cache/'+getFileName(least_frequent_file)).st_size;
            expected_cache_size = cacheHandler.total_directory_size - least_frequent_file_size + file_size
            expected_cache_without_removing_file = cacheHandler.total_directory_size + file_size
        else:
            expected_cache_size = cacheHandler.total_directory_size + file_size
            expected_cache_without_removing_file = cacheHandler.total_directory_size + file_size

        if expected_cache_without_removing_file < 10000000:
            cache[fileName] = 1;
            object = open('Cache/'+getFileName(fileName),'w')
            object.write(file)  
            cacheHandler.total_directory_size = expected_cache_without_removing_file; 
           
        elif expected_cache_size < 10000000:
            os.remove('Cache/'+getFileName(least_frequent_file));
            del cache[least_frequent_file];
            cache[fileName] = 1;
            object = open('Cache/'+getFileName(fileName),'w')
            object.write(file)
            cacheHandler.total_directory_size = expected_cache_size; 
    

class request_handler(BaseHTTPRequestHandler):
    def do_GET(s):
        path = s.path[1:]
        indexPath = False
        if path == '':
            path = 'index.html'
            indexPath = True;
        if path in cache:
            cache[path] = cache[path] + 1 
            file = open('Cache/'+getFileName(path),'rb') 
            file_content = file.read()
            file.close
            try:
		s.send_response(200)
		s.send_header("Content-type", "text/plain")
		s.end_headers()
		s.wfile.write(file_content)
            except:
		pass;
        else:
            
            path = s.path[1:]
            url = 'http://'+origin+':8080'+'/'+path
            try:
                content = urllib2.urlopen(url).read()
    	        s.send_response(200)
		s.send_header("Content-type", "text/plain")
	        s.end_headers()
                s.wfile.write(content)
            except urllib2.URLError as e:
                s.send_error(e.code, e.reason)
                return 
            except urllib2.HTTPError as e:
                s.send_error(e.code, e.reason)
            except:
		pass;
            if indexPath:
                cacheInstance.updateCache('index.html',content)
            else:
                cacheInstance.updateCache(path,content)
            
if ( len(sys.argv) == 5 ) : 
        port = sys.argv[2];
        origin= sys.argv[4]
else:
        print "Incorrect number of argument passed";
        sys.exit();
   
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

if __name__ == '__main__':
    cacheInstance = cacheHandler();
    server = ThreadedHTTPServer(('', int(port)), request_handler)
    server.serve_forever()
    

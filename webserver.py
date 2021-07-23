#%%

import sys, signal
import http.server
import socketserver
import threading 
import cgi
import json
from os import path
import datetime

waiting_refresh = threading.Event()
allowed_ip = {}


with open('./html/head.html','rb') as a:
    head = a.read()
    a.close()
with open('./html/footer.html','rb') as a:
    footer = a.read()
    a.close()






def create_alert(message):
    return str.encode("""<div class="alert">"""+message+"""</div>""")

def create_navbar(handler):
    ip = handler.client_address[0]
    return str.encode("""<ul>
    	<li><a href="index.html" class="inactive" >Home</a></li>
    	<li><a href="messageboard.html" class="inactive" >Message Board</a></li>
    	<li><a href="login.html" class="inactive" >"""+  ('Logged as: '+allowed_ip[ip] if ip in allowed_ip else 'Login')  +"""</a></li>
        </ul>""")


def check_user(name, pwd):
    with open('users.txt') as f:
        return (name+':'+pwd) in f.read()     



class ServerHandler(http.server.SimpleHTTPRequestHandler):        


    """
    funzioni relativa alla creazione di pagine html di vario tipo
    """
    #funzione che prende il content di una pagina da file
    def get_content(self):
        f = open('./contents'+self.path,'rb')
        
        allmex = ""       

        if self.path == '/messageboard.html':
            allmex = "<div class='maindiv'>"
            jf = open('data_file.json',)
            data = json.load(jf)
            
            for i in data['mess']:
                allmex += """<div class="container">
                    <h2>"""+i['sender']+""":</h2>
                    <h2>"""+i['title']+"""</h2>
                    <p>"""+i['message']+"""</p>
                    <span class="time-left">"""+i['time']+"""</span>
                    </div>"""  
            allmex += """<div class="container">
                            <br><br>
                            <h1>Aggiungi un messaggio</h1>
                            <form method="post">
                            title:		<input type="text" name="title"><br><br>
                            message:	<input type="text" name="message"><br><br>
                            <input type="submit" name="newmess" value="newmess" /><br><br>
                            </form>
                        </div>"""
            allmex += '</div>'

        return str.encode(allmex)+f.read()

    # funzione per creare una pagina dal contenuto statico
    def send_static(self):
        f = open('./contents'+self.path,'rb')
        content = head+create_navbar(self)+self.get_content()+footer
        f.close()
        self.send_page(content)

    # funzione per creare una pagina con un messaggio di alert
    def send_alert(self, mex):
        f = open('./contents'+self.path,'rb')
        content = head+create_alert(mex)+create_navbar(self)+self.get_content()+footer
        f.close()
        self.send_page(content)

    # funzione per inviare la pagina html
    def send_page(self, content):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(content)



    """
    funzione per gestire la sessione dell'utente ad ogni suo stato
    """
    def manage_login(self):
        if self.client_address[0] not in allowed_ip:
            self.path = '/login.html'
            self.send_alert('Eseguire il login per accedere ai contenuti.')
        elif self.path == '/login.html':
            self.path = '/logout.html'
            self.send_static()
        else:
            self.send_static()


    """
    funzioni relative alla gestione di richieste get e all'interazione con l'utente tramite form
    """
    # handler per richieste GET
    def do_GET(self):
        self.manage_login()
        

    """
    funzioni relative alla gestione di richieste post e all'interazione con l'utente tramite form
    """
    # funzione che, tramite cgi, viene preso il form con i dati inseriti dall'utente
    def get_form(self):
        return cgi.FieldStorage(    
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD':'POST'}
        )

    # funzione che esegue il logout di un utente tra quelli loggati
    def logout_user(self):
        if self.client_address[0] in allowed_ip:
            del allowed_ip[self.client_address[0]]
        self.path = '/login.html'
        self.send_alert('Eseguire il login per accedere ai contenuti.')

    # funzione che aggiunge un ip tra quelli loggati
    def login_user(self, form):
        user = form.getvalue('user') or 'null'
        password = form.getvalue('password') or 'null'
        # posso fare qui il controllo perche' gli utenti allowed sono sicuramente registrati
        if user in allowed_ip.values():
            self.send_alert('Esiste al corrente una sessione gestita da: '+user+'.')            
        elif check_user(user, password):    
            allowed_ip[self.client_address[0]] = user
            self.path = '/index.html'
            self.send_static()
        else:
            self.send_alert('Credenziali errate.')  

    # funzione per aggiungere un messaggio alla board
    def add_message(self, form):
        title = form.getvalue('title') or 'null'
        content = form.getvalue('message') or 'null'
        users = {
            "title": title,
            "message": content,
            "sender": allowed_ip[self.client_address[0]],
            "time": str(datetime.datetime.now())
        }

        with open('data_file.json','r+') as file:
            file_data = json.load(file)
            file_data["mess"].append(users)
            file.seek(0)
            json.dump(file_data, file, indent = 4)

        self.path = '/messageboard.html'
        self.send_static()

    # handler per richieste POST
    def do_POST(self):
        form = self.get_form()
        if 'logout' in form:
            self.logout_user()
        elif 'login' in form:
            self.login_user(form)
        elif 'newmess' in form:
            self.add_message(form)
            


        

server = socketserver.ThreadingTCPServer(('127.0.0.1', 8080), ServerHandler)

def signal_handler(signal, frame):
    print( 'Exiting http server (Ctrl+C pressed)')
    try:
      if(server):
        server.server_close()
    finally:
      waiting_refresh.set()
      sys.exit(0)


def main():
    server.daemon_threads = True 
    server.allow_reuse_address = True  
    signal.signal(signal.SIGINT, signal_handler)
    try:
      while True:
        server.serve_forever()
    except KeyboardInterrupt:
      pass
    server.server_close()
    
if __name__ == "__main__":
    main()


# %%

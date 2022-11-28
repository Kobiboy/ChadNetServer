import socket
from queue import Queue, Empty
from threading import Thread
import select
import time


HOST = "172.28.29.137"
PORT = 25565
SIZE = 2048
FORMAT = "utf-8"


def newClient(conn, ip, q, online):
    ipAdress, port = ip
    with conn:
        print("Connected with: " + ipAdress)
        while True:
            signup = conn.recv(SIZE).decode()
            name = conn.recv(SIZE).decode()
            password = conn.recv(SIZE).decode()
            if signup == "True":
                login = open("Login.txt")
                if name + " :" not in login.read():
                    login.close()
                    login = open("Login.txt", "a")
                    login.write(name + ' : ' + password + "\n")
                    conn.sendall(bytes("Login successful", FORMAT))
                    print("Sign Up successful")
                    login.close()
                    break
                else:
                    print("Name already in use")
                    conn.sendall(bytes("Try again", FORMAT))
            else:
                login = open("Login.txt", 'r')
                if name + " :" in login.read():
                    login.seek(0)
                    for line in login.readlines():
                        if name in line:
                            if password in line:
                                print("Login successful")
                                conn.sendall(bytes("Login successful", FORMAT))
                                break
                            else:
                                print("Wrong password")
                                conn.sendall(bytes("Try again", FORMAT))
                    else:
                        print("Not good")
                        conn.sendall(bytes("Try again", FORMAT))
                        continue
                    break
                else:
                    print("User not found")
                    conn.sendall(bytes("Try again", FORMAT))
        login.close()
        person = name
        print(f"\nConnected by {person}\n")
        online.put(person)
        t = time.localtime()
        currTime = time.strftime("%H:%M:%S", t)
        message = "(" + currTime + ") " + f"<all>Server: {person} is online now"
        q.put(message)
        onlines = []
        with open("messages.txt", "r+") as f:
            if "<" + person + ">" in f.read():
                f.seek(0)
                d = f.readlines()
                f.seek(0)
                q.put(f"<{person}>New offline messages!:\n")
                for line in d:
                    if "<" + person + ">" in line:
                        q.put(line)
                    else:
                        f.write(line)
            else:
                q.put(f"<{person}>No new messages while offline\n")
            f.truncate()
        while True:
            try:
                for i in range(online.qsize()):
                    tempOnline = online.get(False)
                    onlines.append(tempOnline)
                    online.put(tempOnline)
                for i in range(q.qsize()):
                    message = str(q.get(False))
                    print(message)
                    sender = message.split("<", 1)[1].split(">", 1)[0]
                    login = open("Login.txt")
                    if person == sender:
                        message = message.replace(f"<{person}>", "")
                        conn.send(bytes(message, FORMAT))
                    elif "all" == sender:
                        for _ in range(online.qsize()):
                            personOnline = online.get()
                            online.put(personOnline)
                            newMessage = message.replace("all", personOnline)
                            q.put(newMessage)
                    elif "" == sender:
                        message = None
                    elif sender not in onlines and sender + " :" in login.read():
                        messageFile = open("messages.txt", 'a')
                        messageFile.write(message + "\n")
                        messageFile.close()
                    elif sender + " :" not in login.read():
                        message = f"<{person}>Server: User does not exist!"
                        q.put(message)
                    else:
                        q.put(message)
                    login.close()
            except Empty:
                pass
            except Exception:
                print(Exception)
            else:
                pass
            try:
                s.setblocking(True)
                ready = select.select([conn], [], [], 1)
                if ready[0]:
                    data = conn.recv(SIZE)
                    text = data.decode()
                    if not data:
                        print(f"\n{person} disconnected\n")
                        for i in online.qsize():
                            personOnline = online.get()
                            if person == personOnline:
                                pass
                            else:
                                online.put(personOnline)
                        t = time.localtime()
                        currTime = time.strftime("%H:%M:%S", t)
                        message = "(" + currTime + ") " + f"<all>Server: {person} disconnected"
                        q.put(message)
                        break
                    if text != "":
                        t = time.localtime()
                        currTime = time.strftime("%H:%M:%S", t)
                        message = "(" + currTime + ") " + f"{person}: " + text
                        q.put(message)
            except:
                print(f"\n{person} disconnected\n")
                for i in range(online.qsize()):
                    personOnline = online.get()
                    if person == personOnline:
                        pass
                    else:
                        online.put(personOnline)
                if online.qsize() != 0:
                    t = time.localtime()
                    currTime = time.strftime("%H:%M:%S", t)
                    message = "(" + currTime + ") " + f"<all>Server: {person} disconnected"
                    q.put(message)
                break


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    q = Queue()
    online = Queue()
    s.bind((HOST, PORT))
    s.listen(5)
    while True:
        conn, ip = s.accept()
        Thread(target=newClient, args=(conn, ip, q, online), daemon=True).start()

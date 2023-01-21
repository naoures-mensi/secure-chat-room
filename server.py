import pika
from Crypto.PublicKey import RSA
from encryption_decryption import rsa_encrypt, rsa_decrypt, get_rsa_key


class Server:
    def __init__(self):
        self.channel = None
        self.connection = None
        self.connected_users = {}
        self.rooms = {'room1': [], 'room2': [], 'room3': [], 'room4': []}

    def connect(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        self.channel = self.connection.channel()
        self.receive()

    def receive(self):
        self.channel.queue_declare(queue='main_queue')

        def callback(ch, method, properties, body):
            # Received a Message
            try:
                tokens = body.decode().split('::')
                action = tokens[0]
                tokens[1] = 'amq.' + tokens[1]
                print("[+] Received this ", body)
                self.handle_action(action, tokens[1:])
            except IndexError as index_error:
                print(index_error);
            finally:
                ch.basic_ack(delivery_tag=method.delivery_tag)

        self.channel.basic_consume(queue='main_queue', on_message_callback=callback)
        print('Server Started !! Listening')
        self.channel.start_consuming()

    def handle_action(self, action, tokens):
        if action == 'login':
            # User send this action + his queue name + his name
            queue_name = tokens[0]
            user_name = tokens[1]
            pubkey = tokens[2].encode()
            self.connected_users.setdefault(queue_name, {'username': user_name, 'pubkey': pubkey})
            self.send(queue_name, "connected::")
            for queue in self.connected_users.keys():
                if queue != queue_name:
                    self.send(queue,
                              "connectedUsers::" + ','.join([obj['username'] for obj in self.connected_users.values()]))
        elif action == 'quit':
            # User send his queue name
            queue_name = tokens[0]
            if queue_name in self.connected_users.keys():
                del self.connected_users[queue_name]
                self.send(queue_name, "disconnected::")
                for queue in self.connected_users.keys():
                    if queue != queue_name:
                        self.send(queue, "connectedUsers::" + ','.join(
                            [obj['username'] for obj in self.connected_users.values()]))
                return True
            else:
                self.send(queue_name, "invalid::")
                return False
        elif action == 'getConnectedUsers':
            # return all connected Users names
            queue_name = tokens[0]
            if queue_name in self.connected_users.keys():
                users_names = ','.join([obj['username'] for obj in self.connected_users.values()])
                self.send(queue_name, "connectedUsers::" + users_names)
                return True
            else:
                self.send(queue_name, "notfound::")
                return False
        elif action == 'getUserData':
            # return a user queue name 
            queue_name = tokens[0]
            demanded_user_name = tokens[1]
            for key, val in self.connected_users.items():
                if val['username'] == demanded_user_name:
                    self.send(key, "chosen::" + self.connected_users[queue_name]['username'] + '::' +
                              self.connected_users[queue_name]['pubkey'].decode() + '::' + queue_name)
                    self.send(queue_name,
                              "username::" + str(val['username']) + "::" + str(key) + "::" + val['pubkey'].decode())
                    return True
            self.send(queue_name, "notfound::")
            return False
        elif action == 'getRooms':
            queue_name = tokens[0]
            if queue_name in self.connected_users.keys():
                self.send(queue_name, "rooms::" + ','.join(self.rooms.keys()))
                return True
            self.send(queue_name, 'notfound::')
            return False
        elif action == 'joinRoom':
            queue_name = tokens[0]
            room = tokens[1]
            if queue_name in self.connected_users.keys():
                self.rooms[room].append(queue_name)
                self.send(queue_name, "joinedRoom::" + room + '::')
                return True
            self.send(queue_name, "notfound::")
            return False
        elif action == 'sendToRoom':
            queue_name = tokens[0]
            user_name = self.connected_users[queue_name]['username']
            room = tokens[1]
            # We decrypted the message using the room's private key first
            room_private_key = get_rsa_key("./chatrooms-keys/" + room).export_key()
            message = rsa_decrypt(tokens[2].encode(), room_private_key).decode()
            if queue_name in self.connected_users.keys() and queue_name in self.rooms[room]:
                for queue in self.rooms[room]:
                    # Get pubkey for each user
                    dest_pub_key = self.connected_users[queue]['pubkey']
                    # Encrypt the message with user's public key
                    print(
                        "This is the pubKey of " + self.connected_users[queue][
                            'username'] + ": " + dest_pub_key.decode()[
                                                 :40])
                    encrypted_msg = rsa_encrypt(message, dest_pub_key)
                    self.send(queue, 'roomReceive::' + room + '::' + user_name + '::' + encrypted_msg.decode())
                return True
            else:
                self.send(queue_name, 'notfound::')
                return False
        elif action == 'leaveRoom':
            queue_name = tokens[0]
            room = tokens[1]
            if queue_name in self.connected_users.keys() and queue_name in self.rooms[room]:
                self.rooms[room].remove(queue_name)
                self.send(queue_name, "left::" + room + '::')
                return True
            self.send(queue_name, "notfound::")
            return False
        else:
            print("not handled action : " + action);
            return False;

    def send(self, client_queue, msg):
        self.channel.exchange_declare(exchange='users_exchange', exchange_type='direct')
        self.channel.basic_publish(
            exchange='users_exchange',
            routing_key=client_queue[4:],
            body=msg,
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
            ))


s = Server()
s.connect()

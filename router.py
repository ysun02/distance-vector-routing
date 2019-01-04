#!/usr/bin/python3
'''
COMP 332, Fall 2018
Router that implements distance vector routing algorithm

Example usage:
    python3 router.py PORT NUM_ROUTERS NUM_NBR NBR1 COST1 NBR2 COST2 ...
'''

import socket
import sys
import time

INFINITY = 10000000000

class Router:

    def __init__(self, port, num_nbrs, nbrs, dist, cost):
        self.nbrs = nbrs
        self.dist = dist
        self.cost = cost
        self.num_nbrs = num_nbrs
        self.port = port
        self.timeout = 1 # seconds

    def start(self):
        '''
        Create socket and start main loop for routing algorithm
        '''
        try:
            # Initialize server socket on which to listen for dist
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind(('', self.port))
            sock.settimeout(self.timeout)
        except OSError as e:
            print ("Unable to open server socket: " + str(e))
            sys.exit(0)

        # Main loop for routing algorithm
        self.print_vec(self.dist, True)
        while True:
            time.sleep(1)
            change = self.bellman_ford()
            self.print_vec(self.dist, change)
            self.write_sock(sock, self.dist)

            # Loop number of neighbor times, since all nodes send dv 1/s
            for i in [1,self.num_nbrs]:
                self.read_sock(sock)

    def bellman_ford(self):
        """
        Bellman-ford equation
        """
        change = False
        for router in self.dist:
            for nbr in self.nbrs:
                link = self.cost[nbr]

                # Check whether nbr has dist entry for router
                vec = self.nbrs[nbr]
                if router in vec:
                    dist = link + vec[router]
                else:
                    dist = INFINITY

                # Save new dist only if minimum
                if dist < self.dist[router]:
                    self.dist[router] = dist
                    change = True

        return change

    def write_sock(self, sock, vec):
        '''
        Send my distance vector to all of my neighbors
        '''
        bstr = self.vec_to_bstr(vec)
        for port in self.nbrs:
            if port != self.port:
                sock.sendto(bstr, ('', port))

    def read_sock(self, sock):
        '''
        Read distance vector from neighbors
        '''
        try:
            [bstr, addr] = sock.recvfrom(4096)
        except OSError as e:
            return

        # Update dv of nbr
        port = int(addr[1])
        [flag, vec] = self.bstr_to_vec(port, bstr)
        if flag == True:
            self.nbrs[port] = vec

        # Check whether dv contains new non-nbr nodes
        for port in vec:
            if port != self.port and not port in self.dist:
                self.dist[port] = INFINITY

    def vec_to_bstr(self, vec):
        '''
        Convert dv data structure to binary string
        '''
        data = ''
        for port in vec:
            dist = vec[port]
            data = data + str(port) + ',' + str(dist) + '.'

        hdr = str(len(data)) + ':'
        msg = hdr + data
        bstr = msg.encode('utf-8')
        return bstr

    def bstr_to_vec(self, port, bstr):
        '''
        Convert binary string back to dv data structure
        '''
        try:
            # Extract data from message
            msg = bstr.decode('utf-8')
            hdr_end = msg.index(':')
            msg_len = int(msg[ : hdr_end])
            data_start = hdr_end + 1
            data_end = hdr_end + msg_len + 1
            data = msg[data_start : data_end]

            # Reconstruct dv for nbr
            vec = {}
            entries = data.split('.')
            for entry in entries:
                parts = entry.split(',')
                if len(parts) == 2:
                    port = int(parts[0])
                    dist = int(parts[1])
                    vec[port] = dist

            return [True, vec]
        except ValueError as e:
            return [False, {}]
        except UnicodeDecodeError as e:
            return [False, {}]

    def print_vec(self, vec, change):
        '''
        Only print if no change
        '''

        if change == False:
            return

        print("-------------------------------------------")
        print("Distance vector for node " + str(self.port) + ":")
        print(vec)

def main():

    if len(sys.argv) > 3:
        port = int(sys.argv[1])
        num_routers = int(sys.argv[2])
        num_nbrs = int(sys.argv[3])
        offset = 4

        cost = {} # Dict comprising this node's link costs to nbrs
        nbrs = {} # Dict of dist vec identified by unique port numbers
        dist = {} # Dict comprising this node's dist vec
        cost[port] = 0
        dist[port] = 0

        # Init my distance vector and my nbr link costs
        for i in range(offset, offset+num_nbrs*2, 2):
            nbr = int(sys.argv[i])
            cost[nbr] = int(sys.argv[i+1])
            dist[nbr] = cost[nbr]

        # Init nbr distance vectors
        for p1 in dist:
            if p1 != port:
                nbrs[p1] = {}
                for p2 in dist:
                    nbrs[p1][p2] = INFINITY

        # Start router running
        router = Router(port, num_nbrs, nbrs, dist, cost)
        try:
            router.start()
        except KeyboardInterrupt:
            sys.exit(0)
    else:
        print("Usage: python3 router.py PORT NUM_ROUTERS NUM_NBRS NBR1 COST1 NBR2 COST2...")
        sys.exit(0)


if __name__ == '__main__':
    main()


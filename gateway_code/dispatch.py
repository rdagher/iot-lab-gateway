
"""
'dispatch' module.
"""

import Queue
from threading import Lock

import logging
LOGGER = logging.getLogger()

class Dispatch(object):

    """
    'Dispatch' class handles received messages from the control node.

    It also implement a thread safe send_command function that sends
      a command to the control node and wait for it's answer
    """
    def __init__(self, measures_queue, measures_pkt_mask, io_write = None):
        self.measures_pkt_mask = measures_pkt_mask
        self.measures_queue = measures_queue

        self.queue_control_node = Queue.Queue(1)
        self.io_write = io_write
        self.protect_send = Lock()


    def cb_dispatcher(self, packet):
        """ Forwards the packet tot the appropriate queue depending on
        the packet type """
        # check packet type (first byte)
        # only the first 4 bits
        if (ord(packet[0]) & self.measures_pkt_mask) == self.measures_pkt_mask:
            try:
                self.measures_queue.put_nowait(packet)
            except Queue.Full:
                LOGGER.warning('Measures queue Full')
        else:
            # put the control node's answer into the queue,
            # unlocking `send_command`
            try:
                self.queue_control_node.put_nowait(packet)
            except Queue.Full:
                LOGGER.error('Control node answer queue full')



    def send_command(self, data):
        """
        Send a packet and wait for the answer
        """
        assert self.io_write is not None, 'io_write should be initialized'
        self.protect_send.acquire()

        # remove existing item (old packet lost on timeout?)
        while not self.queue_control_node.empty():
            self.queue_control_node.get_nowait()

        self.io_write(data)
        #Waits for the control node to answer before unlocking send
        #(unlocked by the callback cb_dispatcher
        try:
            answer_cn = self.queue_control_node.get(block=True, timeout=1.0)
        except Queue.Empty:
            answer_cn = None

        self.protect_send.release()
        return answer_cn





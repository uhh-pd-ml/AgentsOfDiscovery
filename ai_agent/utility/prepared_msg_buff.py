class preparedMsgBuff:
    def __init__(self):
        self.prepared_message_buffer = []
    def add_msg(self, msg):
        self.prepared_message_buffer.append(msg)
    
    def get_msg(self):
        return self.prepared_message_buffer
    
    def clear_msg(self):
        self.prepared_message_buffer = []
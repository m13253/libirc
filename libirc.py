#!/usr/bin/env python

import sys
import socket
import string

def stripcomma(s):
    '''Delete the comma if the string starts with a comma.'''
    if s.startswith(':'):
        return s[1:]
    else:
        return s

class IRCConnection:
    def __init__(self):
        self.server=None
        self.nick=None
        self.sock=None
        self.buf=b''
        self.lines=[]
        self.lastRecvFinished=True
    def connect(self, server='irc.freenode.net', port=6667):
        '''Connect to a IRC server.'''
        self.server=server
        self.sock=socket.socket()
        self.sock.connect((server, port))
        self.sock.setblocking(False)
        self.nick=None
        self.buf=b''
        self.lines=[]
        self.lastRecvFinished=True
    def quote(self, s):
        '''Send a specific IRC command. Split multiple commands using \n'''
        for i in s.split('\n'):
            if i:
                self.sock.send(('%s\r\n' % i).encode('utf-8', 'replace'))
    def setpass(self, passwd):
        '''Send password, it should be used before setnick. This password is different from that one sent to NickServ and it is usually unnecessary.'''
        self.quote('PASS %s' % passwd)
    def setnick(self, newnick):
        '''Set nickname.'''
        self.nick=newnick
        self.quote('NICK %s' % newnick)
    def setuser(self, ident=None, realname=None):
        '''Set user ident and real name.'''
        if ident==None:
            ident=self.nick
        if realname==None:
            realname=ident
        self.quote('USER %s %s bla :%s' % (ident, self.server, realname))
    def join(self, channel, key=None):
        '''Join channel. A password is optional.'''
        if key!=None:
            key=' '+key
        else:
            key=''
        self.quote('JOIN %s%s' % (channel, key))
    def part(self, channel, reason=None):
        '''Leave channel. A reason is optional.'''
        if reason!=None:
            reason=' :'+reason
        else:
            reason=''
        self.quote('PART %s%s' % (channel, reason))
    def quit(self, reason='Leaving.'):
        '''Quit and disconnect from server. A reason is optional.'''
        if reason!=None:
            reason=' :'+reason
        else:
            reason=''
        self.quote('QUIT%s' % reason)
        self.sock.close()
        self.sock=None
        self.server=None
        self.nick=None
        self.lastRecvFinished=True
    def say(self, dest, msg):
        '''Send a message to a channel or a private message to a person.'''
        for i in msg.split('\n'):
            self.quote('PRIVMSG %s :%s' % (dest, i))
    def recv(self, size=1024):
        '''Receive stream from server. Do not call it directly, it should be called by parse().'''
        try:
            self.buf+=self.sock.recv(size)
            self.lastRecvFinished=self.buf.endswith(b'\n')
        except socket.error as e:
            if e.errno!=11:
                raise e
    def parse(self):
        '''Receive messages from server and process it. Returning a dictionary or None.'''
        if len(self.lines)<2:
            self.recv()
        if self.buf:
            if not self.lastRecvFinished:
                line=self.buf.split(b'\n', 1)
                if len(line)==2:
                    line, self.buf=line
                else:
                    line=line[0]
                    self.buf=b''
                if len(self.lines)>=1:
                    self.lines.append(self.lines.pop()+line.decode('utf-8', 'replace'))
                else:
                    self.lines.append(line.decode('utf-8', 'replace'))
            if self.buf:
                self.lines+=self.buf.decode('utf-8', 'replace').split('\n')
            self.buf=b''
        if self.lines and len(self.lines)>1:
            line=self.lines.pop(0).rstrip('\r')
            if not line:
                return self.parse()
            try:
                if line.startswith('PING '):
                    self.quote('PONG %s' % line[5:])
                    return {'nick': None, 'ident': None, 'cmd': 'PING', 'dest': None, 'msg': stripcomma(line[5:])}
                cmd=line.split(None, 1)
                nick=cmd.pop(0).split('!', 1)
                if len(nick)>=2:
                    nick, ident=nick
                else:
                    ident=None
                    nick=nick[0]
                nick=stripcomma(nick)
                if cmd!=[]:
                    msg=cmd[0].split(None, 1)
                    cmd=msg.pop(0)
                    if msg!=[]:
                        if msg[0].startswith(':'):
                            dest=None
                            msg=stripcomma(msg[0])
                        else:
                            msg=msg[0].split(None, 1)
                            dest=msg.pop(0)
                            if msg!=[]:
                                msg=stripcomma(msg[0])
                            else:
                                msg=None
                    else:
                        msg=dest=None
                else:
                    msg=dest=cmd=None
                return {'nick': nick, 'ident': ident, 'cmd': cmd, 'dest': dest, 'msg': msg}
            except:
                return {'nick': None, 'ident': None, 'cmd': None, 'dest': None, 'msg': line}
        else:
            return None
    def __del__(self):
        if self.sock:
            self.quit()

# vim: et ft=python sts=4 sw=4 ts=4

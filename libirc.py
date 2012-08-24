#!/usr/bin/env python

import errno
import socket
import sys

# If you want a different value, change libirc.BUFFER_LENGTH after importing.
BUFFER_LENGTH=1024

def stripcomma(s):
    '''Delete the comma if the string starts with a comma.'''
    if s.startswith(':'):
        return s[1:]
    else:
        return s

def rmnl(s):
    return s.replace('\r', '').strip('\n').replace('\n', ' ')
def rmnlsp(s):
    return s.replace('\r', '').replace('\n', '').replace(' ', '')
def rmcr(s):
    return s.replace('\r', '')

class IRCConnection:
    def __init__(self):
        self.server=None
        self.nick=None
        self.sock=None
        self.buf=b''
    def connect(self, server='irc.freenode.net', port=6667):
        '''Connect to a IRC server.'''
        self.server=rmnlsp(server)
        self.sock=socket.socket()
        self.sock.connect((self.server, port))
        self.nick=None
        self.buf=b''
    def quote(self, s):
        '''Send a raw IRC command. Split multiple commands using \\n.'''
        if not self.sock:
            e=socket.error('[errno %d] Socket operation on non-socket' % errno.ENOTSOCK)
            e.errno=errno.ENOTSOCK
            raise e
        sendbuf=b''
        for i in s.split('\n'):
            if i:
                sendbuf+=i.encode('utf-8', 'replace')+b'\r\n'
        if sendbuf:
            try:
                self.sock.sendall(sendbuf)
            except socket.error as e:
                try:
                    self.sock.close()
                finally:
                    self.sock=None
                raise
    def setpass(self, passwd):
        '''Send password, it should be used before setnick(). This password is different from that one sent to NickServ and it is usually unnecessary.'''
        self.quote('PASS %s' % rmnl(passwd))
    def setnick(self, newnick):
        '''Set nickname.'''
        self.nick=rmnlsp(newnick)
        self.quote('NICK %s' % self.nick)
    def setuser(self, ident=None, realname=None):
        '''Set user ident and real name.'''
        if ident==None:
            ident=self.nick
        if realname==None:
            realname=ident
        self.quote('USER %s %s bla :%s' % (rmnlsp(ident), rmnlsp(self.server), rmnl(realname)))
    def join(self, channel, key=None):
        '''Join channel. A password is optional.'''
        if key!=None:
            key=' '+key
        else:
            key=''
        self.quote('JOIN %s%s' % (rmnlsp(channel), rmnl(key)))
    def part(self, channel, reason=None):
        '''Leave channel. A reason is optional.'''
        if reason!=None:
            reason=' :'+reason
        else:
            reason=''
        self.quote('PART %s%s' % (rmnlsp(channel), rmnl(reason)))
    def quit(self, reason='Leaving.'):
        '''Quit and disconnect from server. A reason is optional.'''
        if reason!=None:
            reason=' :'+reason
        else:
            reason=''
        if self.sock:
            try:
                self.quote('QUIT%s' % rmnl(reason))
            except:
                pass
            try:
                self.sock.close()
            except:
                pass
        self.sock=None
        self.server=None
        self.nick=None
    def say(self, dest, msg):
        '''Send a message to a channel or a private message to a person.'''
        for i in msg.split('\n'):
            self.quote('PRIVMSG %s :%s' % (rmnlsp(dest), rmcr(i)))
    def me(self, dest, action):
        '''Send an action message.'''
        for i in action.split('\n'):
            self.say(rmnlsp(dest), '\x01ACTION %s\x01' % i)
    def mode(self, target, newmode=None):
        '''Read or set mode of a nick or a channel.'''
        if newmode!=None:
            if target.startswith('#') or target.startswith('&'):
                newmode=' '+newmode
            else:
                newmode=' :'+newmode
        else:
            newmode=''
        self.quote('MODE %s%s' % (rmnlsp(target), rmnl(newmode)))
    def kick(self, channel, target, reason=None):
        '''Kick a person out of the channel.'''
        if reason!=None:
            reason=' :'+reason
        else:
            reason=''
        self.quote('KICK %s %s%s' % (rmnlsp(channel), rmnlsp(target), rmnl(reason)))
    def away(self, state=None):
        '''Set away status with an argument, or cancal away status without the argument'''
        if state!=None:
            state=' :'+state
        else:
            state=''
        self.quote('AWAY%s' % rmnl(state))
    def invite(self, target, channel):
        '''Invite a specific user to an invite-only channel.'''
        self.quote('INVITE %s %s' % (rmnlsp(target), rmnlsp(channel)))
    def notice(self, dest, msg=None):
        '''Send a notice to a specific user.'''
        if msg!=None:
            for i in msg.split('\n'):
                if i:
                    self.quote('NOTICE %s :%s' % (rmnlsp(dest), rmcr(i)))
                else:
                    self.quote('NOTICE %s' % rmnlsp(dest))
        else:
            self.quote('NOTICE %s' % rmnlsp(dest))
    def topic(self, channel, newtopic=None):
        '''Set a new topic or get the current topic.'''
        if newtopic!=None:
            newtopic=' :'+newtopic
        else:
            newtopic=''
        self.quote('TOPIC %s%s' % (rmnlsp(channel), rmnl(newtopic)))
    def recv(self, block=False):
        '''Receive stream from server. Do not call it directly, it should be called by parse().'''
        if not self.sock:
            e=socket.error('[errno %d] Socket operation on non-socket' % errno.ENOTSOCK)
            e.errno=errno.ENOTSOCK
            raise e
        try:
            if block:
                received=self.sock.recv(BUFFER_LENGTH)
            else:
                received=self.sock.recv(BUFFER_LENGTH, socket.MSG_DONTWAIT)
            if received:
                self.buf+=received
            else:
                self.quit('Connection reset by peer.')
            return True
        except socket.error as e:
            if e.errno in {socket.EAGAIN, socket.EWOULDBLOCK}:
                return False
            else:
                try:
                    self.quit('Network error.')
                finally:
                    self.sock=None
                raise
    def recvline(self, block=False):
        '''Receive a line from server. It calls recv().'''
        while self.buf.find(b'\n')==-1 and self.recv(block):
            pass
        if self.buf.find(b'\n')!=-1:
            line, self.buf=self.buf.split(b'\n', 1)
            return line.rstrip(b'\r').decode('utf-8', 'replace')
        else:
            return None
    def parse(self, block=False, line=None):
        '''Receive messages from server and process it. Returning a dictionary or None.'''
        if line==None:
            line=self.recvline(block)
        if line:
            try:
                if line.startswith('PING '):
                    try:
                        self.quote('PONG %s' % line[5:])
                    finally:
                        return {'nick': None, 'ident': None, 'cmd': 'PING', 'dest': None, 'msg': stripcomma(line[5:])}
                if line.startswith(':'):
                    cmd=line.split(' ', 1)
                    nick=cmd.pop(0).split('!', 1)
                    if len(nick)>=2:
                        nick, ident=nick
                    else:
                        ident=None
                        nick=nick[0]
                    nick=stripcomma(nick)
                else:
                    nick=None
                    ident=None
                    if line=="":
                        cmd=[]
                    else:
                        cmd=[line]
                if cmd!=[]:
                    msg=cmd[0].split(' ', 1)
                    cmd=msg.pop(0)
                    if msg!=[]:
                        if msg[0].startswith(':'):
                            dest=None
                            msg=stripcomma(msg[0])
                        else:
                            msg=msg[0].split(' ', 1)
                            dest=msg.pop(0)
                            if cmd!='KICK':
                                if msg!=[]:
                                    msg=stripcomma(msg[0])
                                else:
                                    msg=None
                            else:
                                if msg!=[]:
                                    msg=msg[0].split(' ', 1)
                                    dest2=msg.pop(0)
                                    if msg!=[]:
                                        msg=stripcomma(msg[0])
                                    else:
                                        msg=None
                                    dest=(dest, dest2)
                                else:
                                    msg=None
                                    dest=(None, dest)
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

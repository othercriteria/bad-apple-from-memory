#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Daniel Klein
"""A memory-only silhouette music film. All geometry and sound are generated here."""
from __future__ import annotations
import argparse
import json
import math
import subprocess
import wave
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

BPM = 138
BEAT = 60 / BPM
DURATION = 504 * BEAT
TAU = 2 * math.pi
OUT = Path(__file__).resolve().parent.parent / 'output'


def ease(x):
    x = max(0, min(1, x))
    return x*x*(3-2*x)


def curve(points, steps=8):
    """Closed Catmull–Rom contour, for rounded, expressive silhouettes."""
    pts = []
    for i in range(len(points)):
        p0, p1, p2, p3 = [points[j % len(points)] for j in (i-1,i,i+1,i+2)]
        for k in range(steps):
            t = k/steps
            pts.append(tuple(.5*((2*p1[d])+(-p0[d]+p2[d])*t+(2*p0[d]-5*p1[d]+4*p2[d]-p3[d])*t*t+(-p0[d]+3*p1[d]-3*p2[d]+p3[d])*t*t*t) for d in (0,1)))
    return pts


class Canvas:
    def __init__(self, size, bg=255):
        self.im = Image.new('L', size, bg)
        self.d = ImageDraw.Draw(self.im)
        self.k = size[0]/960
        self.bg, self.fg = bg, 255-bg
        self.stack = [(0,0,1,0,1)]

    def push(self,x=0,y=0,s=1,a=0,flip=1):
        self.stack.append((x,y,s,a,flip))

    def pop(self): self.stack.pop()

    def point(self,p):
        x,y=p
        for tx,ty,s,a,f in reversed(self.stack):
            x*=f
            x,y=s*(x*math.cos(a)-y*math.sin(a))+tx,s*(x*math.sin(a)+y*math.cos(a))+ty
        return (round(x*self.k),round(y*self.k))

    def poly(self,pts,c=None,smooth=False):
        if smooth: pts=curve(pts)
        self.d.polygon([self.point(p) for p in pts],fill=self.fg if c is None else c)

    def line(self,pts,w=3,c=None):
        sc=math.prod(p[2] for p in self.stack)
        self.d.line([self.point(p) for p in pts],fill=self.fg if c is None else c,width=max(1,round(w*self.k*sc)),joint='curve')

    def oval(self,x,y,rx,ry=None,c=None):
        ry=rx if ry is None else ry
        self.poly([(x+rx*math.cos(i*TAU/48),y+ry*math.sin(i*TAU/48)) for i in range(48)],c)

    def ring(self,x,y,r,w=3,c=None):
        self.line([(x+r*math.cos(i*TAU/100),y+r*math.sin(i*TAU/100)) for i in range(101)],w,c)


def bow(c,x,y,s=1,a=0):
    c.push(x,y,s,a)
    c.poly([(-4,0),(-38,-23),(-42,16),(-10,13),(0,5),(11,14),(42,16),(38,-23),(4,0)])
    c.oval(0,1,7,9)
    c.pop()


def apple(c,x,y,s=1,a=0):
    c.push(x,y,s,a)
    c.poly([(0,-22),(-23,-31),(-40,-18),(-42,6),(-30,33),(-12,44),(0,39),(15,44),(34,29),(44,2),(37,-20),(18,-30)],smooth=True)
    c.line([(0,-22),(2,-37),(11,-47)],6)
    c.poly([(4,-35),(14,-50),(33,-46),(21,-33)],smooth=True)
    c.pop()


def knife(c,x,y,s=1,a=0):
    c.push(x,y,s,a)
    c.poly([(-4,21),(-4,-15),(0,-63),(5,-15),(4,21)])
    c.line([(-12,20),(12,20)],5)
    c.line([(0,20),(0,46)],8)
    c.pop()


def fan(c,x,y,s=1,a=0):
    c.push(x,y,s,a)
    c.poly([(0,0)]+[(100*math.cos(v),100*math.sin(v)) for v in np.linspace(-2.8,-.35,50)])
    for v in np.linspace(-2.8,-.35,9):
        c.line([(0,-2),(94*math.cos(v),94*math.sin(v))],2,c.bg)
    c.pop()


def wings(c,t,crystal=False):
    for side in [-1,1]:
        c.push(0,-65,flip=side)
        flap=math.sin(t*2)*15
        if crystal:
            c.line([(15,0),(75,-45),(138,-36),(184,-65+flap)],7)
            for i in range(7):
                x=45+i*21;y=-22-i*4+flap*i/7
                c.line([(x,y-15),(x,y+25)],2)
                c.poly([(x,y+13),(x-9,y+30),(x,y+51),(x+9,y+30)])
        else:
            c.poly([(8,5),(52,-45),(91,-83+flap),(137,-97+flap),(119,-58),(172,-35),(157,-4),(135,-23),(116,-15),(100,12),(77,-6),(58,7),(41,37),(27,15)],smooth=False)
        c.pop()


def person(c,x,y,s,t,kind='shrine',pose='dance',flip=1):
    """Articulated girl in local coordinates: head -115, feet +165."""
    bounce=math.sin(t*TAU/BEAT/2)*2
    sway=math.sin(t*2)*.055
    if pose=='fly': sway-=.22
    c.push(x,y+bounce*s,s,sway,flip)
    longhair=kind in ['shrine','witch','princess','rabbit','flower','gap']
    # Hair mass and independently flowing pointed locks.
    wind=math.sin(t*2.8)*8
    c.poly([(-34,-133),(-43,-99),(-40,-55),(-51+wind,15 if longhair else -37),(-22,0 if longhair else -47),(10,-29),(32+wind,22 if longhair else -34),(45,-60),(39,-126),(15,-153),(-11,-156)],smooth=True)
    for i in range(4):
        xx=-34+i*21
        c.poly([(xx,-102),(xx+15,-92),(xx+22+wind,5 if longhair else -31),(xx+4,-44)])
    if kind in ['vampire','crystal']: wings(c,t,kind=='crystal')
    if kind=='crow':
        for side in [-1,1]:
            c.push(0,-40,flip=side,a=.07*math.sin(t*3))
            for j in range(10):
                c.poly([(12,0),(65+j*8,-92+j*8),(159-j*4,-74+j*13),(140-j*5,-61+j*12),(64,30)],smooth=False)
            c.pop()
    # Legs move in opposite arcs, boots retain a pointed profile.
    for side in [-1,1]:
        leg_angle=side*(.10+.15*math.sin(t*2))
        if pose=='fly':leg_angle+=.50*math.sin(t*3+side*1.6)
        c.push(side*19,72,a=leg_angle)
        c.poly([(-9,0),(10,0),(8,46),(-8,46)],smooth=True)
        c.push(0,40,a=(-.5-.4*math.sin(t*3+side)) if pose=='fly' else -.08)
        c.poly([(-8,0),(8,0),(7,25),(5,39),(18,47),(20,55),(-11,55),(-12,40)],smooth=True)
        c.line([(-9,27),(8,27)],3,c.bg)
        c.pop()
        c.pop()
    # Fitted bodice, flared skirt, scalloped hem.
    c.poly([(-16,-84),(-31,-67),(-25,-32),(-20,-15),(22,-15),(29,-57),(17,-84)],smooth=True)
    hem=[]
    for j in range(13):
        xx=-75+j*12.5
        hem.append((xx,77+5*math.sin(j*math.pi/2+t*3)+8*(xx/75)**2))
    c.poly([(-22,-24),(-45,16),(-75,77)]+hem+[(75,77),(45,14),(20,-24)])
    c.line([(-20,-13),(20,-13)],3,c.bg)
    if kind in ['maid','witch']:
        c.poly([(-15,-56),(15,-56),(13,-15),(44,62),(23,72),(-24,72),(-43,63),(-12,-15)],c.bg,smooth=True)
        c.poly([(-9,-60),(9,-60),(8,-22),(-8,-22)])
    if kind in ['shrine','ghost','princess']:
        c.poly([(-16,-80),(0,-48),(16,-80),(6,-74),(0,-60),(-6,-74)],c.bg)
        c.poly([(-3,-54),(-9,-30),(0,-19),(9,-30),(3,-54)],c.bg)
    # Arm choreography: elbow bends and sleeves follow the gesture.
    for side in [-1,1]:
        if pose=='reach': a=side*(-.7)+.2*math.sin(t*2)
        elif pose=='fly': a=side*1.2+.15*math.sin(t*2)
        elif pose=='hold': a=-.9 if side==1 else .2
        else: a=side*(1.05+1.0*math.sin(t*1.65+side*.7))
        c.push(side*24,-67,a=a)
        c.poly([(-9,-2),(10,-2),(11,34),(-10,37)],smooth=True)
        if kind in ['shrine','ghost','princess','gap']:
            c.poly([(-12,12),(13,10),(22,70),(-24,65)])
            c.line([(-21,58),(19,62)],3,c.bg)
        c.push(0,32,a=side*(.5+.45*math.sin(t*1.7)))
        c.poly([(-7,0),(7,0),(6,37),(3,47),(-6,46),(-8,34)],smooth=True)
        # Small separated fingers instead of circles for hands.
        for finger in range(3):
            c.line([(-5+finger*4,35),(-8+finger*5,49-finger*2)],3)
        if kind=='maid' and side==1: knife(c,0,41,.55,1.4)
        if kind=='flower' and side==1: c.line([(0,40),(0,-155)],4)
        if kind=='sword' and side==1:
            c.line([(0,42),(0,-140)],6)
            c.line([(-15,14),(15,14)],5)
        if kind=='ghost' and side==1: fan(c,0,40,.7,math.pi)
        c.pop();c.pop()
    # Neck and face, with a small profile nose and asymmetrical fringe.
    c.poly([(-10,-99),(10,-99),(12,-74),(-13,-74)])
    c.poly([(-28,-133),(-12,-150),(13,-149),(29,-133),(30,-117),(38,-109),(29,-104),(25,-91),(11,-83),(-12,-91),(-28,-113)],smooth=True)
    c.poly([(-31,-133),(-7,-146),(25,-136),(17,-111),(8,-126),(1,-108),(-5,-129),(-18,-111),(-23,-128)])
    # Character-specific head silhouettes and negative-space ribbons.
    if kind=='shrine':
        bow(c,-1,-153,1.05,.05)
        for side in [-1,1]:
            c.poly([(side*28,-107),(side*39,-104),(side*43,-85),(side*29,-88)],c.bg)
    elif kind=='witch':
        c.poly([(-46,-148),(-26,-167),(-12,-220),(4,-231),(24,-211),(17,-186),(43,-148)])
        c.oval(0,-146,69,13)
        c.line([(-28,-164),(30,-157)],7,c.bg)
        bow(c,31,-161,.48,.2)
    elif kind in ['maid','sword']:
        for j in range(7):
            a=-2.8+j*.4
            c.oval(38*math.cos(a),-123+33*math.sin(a),8,7)
        c.line([(-31,-141),(0,-155),(29,-140)],3,c.bg)
        bow(c,-29,-106,.33)
    elif kind in ['vampire','crystal','princess','ghost']:
        c.poly([(-44,-141),(-30,-164),(12,-175),(38,-155),(45,-140)],smooth=True)
        for j in range(8):c.oval(-37+j*11,-140,8,6)
        bow(c,27,-146,.5)
        if kind=='ghost':
            c.poly([(-9,-161),(0,-181),(12,-161)],c.bg)
            c.line([(-3,-165),(1,-171),(6,-164)],2)
    elif kind=='rabbit':
        c.poly([(-21,-145),(-34,-213),(-22,-222),(-7,-153)],smooth=True)
        c.poly([(8,-151),(17,-225),(31,-231),(30,-190),(22,-147)],smooth=True)
    elif kind=='oni':
        c.poly([(-31,-140),(-41,-184),(-12,-150)])
        c.poly([(17,-149),(40,-180),(32,-132)])
        bow(c,-38,-86,.5)
    elif kind=='crow':
        c.poly([(-18,-151),(-15,-170),(11,-170),(19,-151)])
        c.line([(-13,-161),(13,-161)],3,c.bg)
    elif kind=='gap':
        c.oval(0,-149,52,14)
        c.poly([(-29,-152),(-23,-182),(22,-182),(33,-150)],smooth=True)
        bow(c,30,-156,.5)
    c.pop()


# 31 shots, timed in beats. Deliberately authored without consulting a shot list.
SHOTS = [
    (16,'apple'),(16,'shrine'),(16,'witch'),(16,'flight'),
    (16,'books'),(16,'maid'),(16,'clock'),(16,'knives'),
    (16,'vampire'),(16,'crystal'),(16,'sword'),(16,'ghost'),
    (16,'petals'),(16,'rabbit'),(16,'bamboo'),(16,'princess'),
    (16,'fire'),(16,'oni'),(16,'dolls'),(16,'flower'),
    (16,'umbrella'),(16,'gap'),(16,'crow'),(16,'mountain'),
    (16,'duet'),(16,'orbit'),(16,'run'),(16,'reach'),
    (16,'fall'),(16,'return'),(24,'last_apple')]
STARTS=np.cumsum([0]+[b for b,_ in SHOTS])*BEAT


def scene(c,idx,u,t):
    name=SHOTS[idx][1]
    p=u/(SHOTS[idx][0]*BEAT)
    # Slow camera moves keep each pose alive beyond its articulated movement.
    if name=='apple':
        s=.2+3.8*ease(p)
        apple(c,480,330,s,-.5+.8*p)
        if p>.60:
            c.push(480,510,2.2*ease((p-.6)/.4))
            c.poly([(-230,95),(-72,26),(-28,-3),(21,-19),(61,-13),(66,-4),(16,7),(48,10),(52,19),(7,28),(-21,51),(-159,137)],smooth=True)
            c.pop()
    elif name=='shrine':
        person(c,475+35*math.sin(p*math.pi),405,1.62,u,'shrine','reach')
        for j in range(7):
            c.push(150+j*110,80+30*math.sin(u+j),.7,a=.2*math.sin(u+j))
            c.line([(0,-160),(0,0)],2)
            c.poly([(0,0),(19,13),(7,29),(23,40),(3,64),(9,38),(-5,28),(8,13)])
            c.pop()
    elif name in ['witch','flight']:
        if name=='flight':
            c.oval(725,190,136)
            c.oval(681,168,127,c=c.bg)
            for j in range(28):
                xx=(j*113-u*(40+j%4*40))%1150-100; yy=(j*73)%700
                c.line([(xx,yy),(xx+20+j%3*35,yy)],2)
            c.push(470,380,a=-.12)
            c.line([(-290,85),(215,85)],10)
            c.poly([(-210,82),(-316,50),(-345,118),(-213,99)])
            for j in range(5): c.line([(-330,65+j*11),(-221,87)],2,c.bg)
            c.pop()
        person(c,480+80*math.sin(u*.6),385,1.4,u,'witch','fly' if name=='flight' else 'dance',-1)
    elif name=='books':
        for j in range(13):
            xx=(j*113+u*28)%1150-100; yy=(j*173)%780-40
            c.push(xx,yy,.6+(j%3)*.3,a=.3*math.sin(u+j))
            c.poly([(-45,-29),(0,-18),(45,-29),(45,30),(0,42),(-45,30)])
            c.line([(0,-16),(0,36)],3,c.bg)
            for k in range(3):c.line([(-35,-15+k*13),(-8,-8+k*13)],2,c.bg)
            c.pop()
        person(c,490,400,1.65,u,'princess','hold')
    elif name in ['maid','clock','knives']:
        if name in ['clock','maid']:
            cx=480 if name=='clock' else 760;cy=340;r=280 if name=='clock' else 220
            c.ring(cx,cy,r,7);c.ring(cx,cy,r-16,2)
            for j in range(60):
                a=j*TAU/60
                c.line([(cx+(r-25)*math.sin(a),cy+(r-25)*math.cos(a)),(cx+(r-(48 if j%5==0 else 34))*math.sin(a),cy+(r-(48 if j%5==0 else 34))*math.cos(a))],5 if j%5==0 else 2)
            for a,length in [(u*.7,r*.75), (u*.12,r*.5)]:
                c.line([(cx,cy),(cx+length*math.sin(a),cy-length*math.cos(a))],8)
            c.oval(cx,cy,13)
        if name=='knives':
            for j in range(24):
                a=j*TAU/24+u*.18;r=270+35*math.sin(u*1.5+j)
                knife(c,480+r*math.cos(a),360+r*math.sin(a),.8,a+math.pi/2)
        person(c,400 if name=='maid' else 480,400,1.45 if name=='clock' else 1.6,u,'maid','dance')
    elif name in ['vampire','crystal']:
        c.oval(480,310,230,c=c.fg)
        c.oval(460,295,219,c=c.bg)
        person(c,480,410,1.6,u,name,'reach')
        for j in range(14):
            xx=(j*149+u*35)%1040-40;yy=(j*79-u*18)%760-20
            c.push(xx,yy,.20+.10*(j%3),a=math.sin(j+u)*.3)
            c.poly([(-45,0),(-33,-19),(-12,-5),(0,-13),(12,-5),(33,-19),(45,0),(22,-4),(13,8),(0,2),(-13,8),(-22,-4)])
            c.pop()
    elif name=='sword':
        person(c,480,410,1.7,u,'sword','reach')
        a=-1+2*ease(p)
        c.push(480,360,a=a)
        c.poly([(-650,-12),(580,-3),(650,2),(-580,13)])
        c.pop()
        for j in range(4):
            q=u*.9+j*1.5
            x=480+300*math.cos(q);y=330+160*math.sin(q)
            c.poly([(x,y-23),(x-32,y),(x-25,y+30),(x+19,y+34),(x+64,y-4),(x+8,y+10)],smooth=True)
    elif name in ['ghost','petals']:
        if name=='ghost':person(c,470,405,1.65,u,'ghost','dance')
        else:
            # Branches frame an airy, distant figure.
            c.line([(-20,600),(90,410),(145,230),(300,110),(415,-10)],17)
            c.line([(95,403),(245,305),(353,278)],9)
            c.line([(148,230),(90,98),(105,-10)],8)
            person(c,620,450,1.17,u,'ghost','hold')
        for j in range(65):
            x=(j*97+u*(20+j%7))%1050-45;y=(j*47+u*(35+j%9))%810-45
            c.push(x,y,.4+(j%5)*.12,a=u+j)
            c.poly([(0,-8),(-8,-2),(-4,9),(0,4),(5,8),(9,-2)],smooth=True)
            c.pop()
    elif name in ['rabbit','bamboo','princess']:
        if name!='princess':
            for j in range(7):
                x=(j*187-u*(10 if name=='bamboo' else 2))%1260-150
                c.push(x,0,a=.025*math.sin(j))
                c.poly([(0,-30),(14,-30),(11,760),(-6,760)])
                for k in range(6):
                    y=k*137+j%3*29
                    c.line([(-5,y),(16,y)],3,c.bg)
                    for side in [-1,1]:
                        c.poly([(8,y),(side*80,y-55),(side*54,y-7)],smooth=True)
                c.pop()
        else:
            c.ring(480,330,265,2)
            for j in range(8):
                a=j*TAU/8+u*.1
                c.oval(480+245*math.cos(a),330+245*math.sin(a),9)
        if name!='princess':
            c.oval(480,363,178,302,c.bg)
        person(c,480,410,1.55,u,'princess' if name=='princess' else 'rabbit','dance')
    elif name=='fire':
        for j in range(19):
            x=j*58-40
            h=140+100*math.sin(j*2.3+u*2)
            c.poly([(x-40,730),(x-28,630),(x+18,720-h),(x+10,580-h),(x+52,655),(x+68,725)],smooth=True)
        person(c,480,380,1.5,u,'princess','reach')
        for j in range(36):
            xx=(j*137+20*math.sin(u+j))%960; yy=720-(j*31+u*80)%800
            c.poly([(xx,yy-12),(xx-3,yy),(xx,yy+8),(xx+5,yy)])
    elif name=='oni':
        person(c,490,410,1.75,u,'oni','dance')
        for j in range(12):
            x=160+j*58;y=555+60*math.sin(j*.45+u)
            c.ring(x,y,18,5)
        c.push(188,535,.8,a=.2*math.sin(u))
        c.poly([(-13,-44),(13,-44),(16,-24),(35,-5),(25,37),(-25,37),(-35,-5),(-16,-24)],smooth=True)
        c.line([(-15,-40),(15,-40)],6);c.pop()
    elif name=='dolls':
        person(c,480,410,1.6,u,'maid','reach')
        for j in range(6):
            a=j*TAU/6+u*.22
            x=480+330*math.cos(a);y=350+220*math.sin(a)
            c.line([(x-15,-10),(x-15,y-50)],1)
            c.line([(x+15,-10),(x+15,y-50)],1)
            person(c,x,y,.43,u+j,'shrine','fly',(-1)**j)
    elif name=='flower':
        for j in range(9):
            x=j*133-55;y=520+70*math.sin(j*2)
            c.line([(x,740),(x,y)],9)
            for k in range(12):
                a=k*TAU/12+u*.03
                c.push(x+45*math.cos(a),y+45*math.sin(a),a=a)
                c.oval(0,0,27,10);c.pop()
            c.oval(x,y,25)
        person(c,480,385,1.6,u,'flower','hold')
    elif name in ['umbrella','gap']:
        person(c,480,420,1.6,u,'gap','hold')
        c.push(550,215,a=.12*math.sin(u))
        c.line([(0,-20),(0,300)],5)
        c.poly([(-235,0),(-187,-65),(-100,-122),(0,-150),(100,-122),(187,-65),(235,0),(174,-16),(119,4),(61,-13),(0,6),(-61,-13),(-119,4),(-174,-16)],smooth=True)
        for x in [-170,-85,0,85,170]:c.line([(0,-143),(x,-15)],2,c.bg)
        c.pop()
        if name=='gap':
            for j in range(6):
                xx=(j*183)%1000; yy=100+(j*197)%570
                c.push(xx,yy,a=.3*math.sin(u+j))
                c.poly([(-90,0),(-40,-18),(35,-13),(90,0),(36,17),(-35,20)],smooth=True)
                for k in range(3):
                    c.oval(-40+k*38,0,12,7,c.bg);c.oval(-40+k*38,0,3,7)
                c.pop()
    elif name in ['crow','mountain']:
        if name=='mountain':
            c.poly([(0,540),(170,280),(310,440),(570,160),(750,410),(850,290),(960,470),(960,720),(0,720)])
            c.poly([(490,284),(570,160),(634,249),(586,231),(562,254),(546,237)],c.bg)
            # Flying figure in a contrasting circular window.
            c.oval(480,310,205,c=c.bg)
        person(c,480,390 if name=='crow' else 340,1.45,u,'crow','fly')
        for j in range(18):
            xx=(j*157+u*90)%1150-100;yy=(j*89-u*20)%790-30
            c.push(xx,yy,.65,a=u*.8+j)
            c.poly([(0,-35),(-9,-14),(-7,19),(0,36),(9,12),(8,-19)],smooth=True)
            c.line([(0,-20),(0,30)],2,c.bg);c.pop()
    elif name=='duet':
        # White and black characters face one another across a moving divide.
        split=480+80*math.sin(p*TAU)
        c.poly([(split,-10),(970,-10),(970,730),(split,730)])
        person(c,split-180,410,1.45,u,'shrine','reach')
        old=c.fg,c.bg;c.fg,c.bg=c.bg,c.fg
        person(c,split+180,410,1.45,u+.6,'witch','reach',-1)
        c.fg,c.bg=old
    elif name=='orbit':
        for j,kind in enumerate(['shrine','witch','maid','ghost','rabbit','crow','crystal','oni']):
            a=j*TAU/8-u*.23
            person(c,480+300*math.cos(a),350+215*math.sin(a),.5,u+j,kind,'reach',1 if math.cos(a)<0 else -1)
        apple(c,480,345,1.35+.15*math.sin(u*TAU/BEAT),u*.2)
    elif name=='run':
        for j in range(18):
            xx=(j*97-u*240)%1150-100; yy=(j*83)%720
            c.line([(xx,yy),(xx+70,yy)],2)
        person(c,355,395,1.5,u*2,'shrine','fly')
        person(c,695,415,1.1,u*2+.8,'witch','fly')
    elif name=='reach':
        # Extreme close-up of two reaching hands; fingers nearly touch.
        gap=140*(1-ease(p))
        for side in [-1,1]:
            c.push(480+side*gap,360,2.0,flip=-side)
            c.poly([(-290,60),(-128,14),(-67,-15),(-31,-20),(-8,-15),(8,-8),(4,-2),(-27,-6),(-46,1),(-12,5),(14,13),(12,20),(-24,15),(-45,19),(-17,25),(2,34),(-2,40),(-47,31),(-76,43),(-109,51),(-270,114)],smooth=True)
            c.pop()
        apple(c,480,240+80*p,.8,math.sin(u)*.1)
    elif name=='fall':
        for j in range(8):
            a=j*TAU/8+u*.2
            knife(c,480+330*math.cos(a),360+300*math.sin(a),1,a)
        c.push(480,350,a=p*math.pi*.85)
        person(c,0,0,1.6-.6*p,u,'shrine','fly')
        c.pop()
    elif name=='return':
        person(c,340,420,1.6,u,'shrine','hold')
        person(c,685,410,1.5,u,'witch','hold',-1)
        apple(c,490,300-90*math.sin(p*math.pi),.9,u*.5)
    elif name=='last_apple':
        apple(c,480,345,2.5*(1-ease(max(0,(p-.6)/.4)))+.01,p*.2)
        if p>.32:
            # A bite disappears into the background; the remaining fruit closes to a dot.
            ss=2.5*(1-ease(max(0,(p-.6)/.4)))+.01
            c.oval(480+36*ss,345-12*ss,18*ss*ease((p-.32)/.10),c=c.bg)


def frame(t,size):
    idx=min(len(SHOTS)-1,int(np.searchsorted(STARTS,t,side='right')-1))
    u=t-STARTS[idx]
    bg=0 if idx in [3,6,8,9,11,12,15,16,20,21,23,25,28] else 255
    c=Canvas(size,bg)
    # Shot-specific dolly and pan: alternate full figures with cropped portraits.
    p=u/(SHOTS[idx][0]*BEAT)
    cameras={
        1:(1.50,1.0,480,290), 2:(1.0,1.32,480,295),
        5:(1.65,1.08,400,270), 7:(1.0,1.25,480,330),
        8:(1.22,1.0,480,320), 10:(1.20,1.65,480,325),
        11:(1.0,1.24,480,320), 13:(1.45,1.0,480,285),
        15:(1.0,1.6,480,275), 17:(1.30,1.0,480,345),
        19:(1.45,1.0,480,295), 21:(1.0,1.3,480,330),
        22:(1.15,1.0,480,330), 26:(1.05,1.25,480,345),
        29:(1.2,1.0,480,345),
    }
    if idx in cameras:
        z0,z1,cx,cy=cameras[idx];z=z0+(z1-z0)*ease(p)
        c.push(480-cx*z,360-cy*z,z)
    scene(c,idx,u,t)
    if idx in cameras:c.pop()
    # Organic iris transitions: an expanding apple-shaped black/white field.
    remaining=STARTS[idx+1]-t
    if idx<len(SHOTS)-1 and remaining<.42:
        q=ease(1-remaining/.42)
        nextbg=0 if idx+1 in [3,6,8,9,11,12,15,16,20,21,23,25,28] else 255
        if nextbg==bg:
            # A diagonal wipe to the next live composition, no long blank cuts.
            nxt=Canvas(size,nextbg);scene(nxt,idx+1,0,t)
            mask=Image.new('L',size,0);d=ImageDraw.Draw(mask)
            x=(size[0]+size[1])*q
            d.polygon([(0,0),(x,0),(x-size[1],size[1]),(0,size[1])],fill=255)
            c.im=Image.composite(nxt.im,c.im,mask)
        else:
            c.fg=nextbg
            apple(c,480,350,q*23,0)
    return c.im


# Monophonic remembered contour, arranged as an instrumental electronic cover.
# Semitone offsets relative to Eb4. Durations are eighth notes.
VERSE=[
 [(0,1),(2,1),(3,1),(5,1),(7,2),(12,1),(10,1),(7,2),(5,1),(3,1),(2,2),(-2,2)],
 [(0,1),(2,1),(3,1),(5,1),(7,2),(5,1),(3,1),(2,2),(0,1),(2,1),(3,2),(2,2)],
 [(0,1),(2,1),(3,1),(5,1),(7,2),(12,1),(10,1),(7,2),(5,1),(3,1),(2,2),(-2,2)],
 [(0,1),(2,1),(3,1),(5,1),(7,2),(5,1),(3,1),(2,2),(3,1),(2,1),(0,4)],
]
CHORUS=[
 [(7,1),(7,1),(7,1),(5,1),(7,2),(10,2),(12,2),(10,1),(7,1),(5,2),(3,2)],
 [(5,1),(5,1),(5,1),(3,1),(5,2),(7,2),(10,2),(7,1),(5,1),(3,2),(2,2)],
 [(3,1),(3,1),(3,1),(2,1),(3,2),(5,2),(7,2),(5,1),(3,1),(2,2),(0,2)],
 [(2,1),(3,1),(5,1),(7,1),(5,2),(3,2),(2,2),(-2,2),(0,4)],
]


def soundtrack(path,duration):
    sr=44100;n=round(duration*sr)
    mix=np.zeros((n,2),np.float32)
    rng=np.random.default_rng(1988)
    def add(at,sig,gain=1,pan=0):
        i=round(at*sr)
        if i>=n:return
        if i<0:sig=sig[-i:];i=0
        sig=sig[:n-i]*gain
        mix[i:i+len(sig),0]+=sig*math.sqrt((1-pan)/2)
        mix[i:i+len(sig),1]+=sig*math.sqrt((1+pan)/2)
    def tone(midi,length,voice='lead'):
        tt=np.arange(round(length*sr),dtype=np.float32)/sr
        f=440*2**((midi-69)/12)
        phase=TAU*f*tt+.014*np.sin(TAU*5.2*tt)
        if voice=='lead':
            sig=sum(np.sin(phase*h)*(.68**(h-1))/h for h in range(1,8))
            sig+=.20*np.sin(phase*1.003)
            env=np.minimum(tt/.012,1)*np.minimum(np.maximum(length-tt,0)/.045,1)*(.8+.2*np.exp(-tt*9))
        elif voice=='bass':
            sig=np.sin(phase)+.32*np.sin(phase*2)+.14*np.sin(phase*3)
            env=np.minimum(tt/.006,1)*np.exp(-tt*3)*np.minimum(np.maximum(length-tt,0)/.02,1)
        elif voice=='bell':
            sig=np.sin(phase)+.35*np.sin(phase*2)+.14*np.sin(phase*3)
            env=np.minimum(tt/.004,1)*np.exp(-tt*7)*np.minimum(np.maximum(length-tt,0)/.03,1)
        else:
            sig=(np.sin(phase)+np.sin(phase*1.004)+np.sin(phase*.997))/3
            env=np.minimum(tt/.15,1)*np.minimum(np.maximum(length-tt,0)/.25,1)
        return (sig*env).astype(np.float32)
    # Four-on-the-floor rhythm, open hats, snare, and small phrase fills.
    for b in range(math.ceil(duration/BEAT)):
        at=b*BEAT
        breakdown=240<=b<272
        if not breakdown and b<496:
            tt=np.arange(int(sr*.32))/sr
            phase=TAU*(46*tt+(140-46)*.023*(1-np.exp(-tt/.023)))
            kick=np.sin(phase)*np.exp(-tt*14)+rng.normal(0,.09,len(tt))*np.exp(-tt*170)
            add(at,kick,.52)
            if b%2==1:
                tt=np.arange(int(sr*.22))/sr
                noise=rng.normal(0,1,len(tt));noise=np.concatenate([[0],np.diff(noise)])
                snare=(noise*.28+np.sin(TAU*185*tt)*.28)*np.exp(-tt*20)
                add(at,snare,.34)
            for off in [.0,.5]:
                length=.11 if off else .055
                tt=np.arange(int(sr*length))/sr
                noise=rng.normal(0,1,len(tt));noise=np.concatenate([[0],np.diff(noise)])
                add(at+off*BEAT,noise*np.exp(-tt*(35 if off else 75)),.055, .30 if off else -.3)
        if b%32==0 and b<490:
            tt=np.arange(int(sr*1.5))/sr
            noise=rng.normal(0,1,len(tt))
            add(at,noise*np.exp(-tt*4)*(.5+.5*np.sin(TAU*7300*tt)),.09,-.25)
    # Eb minor / B / Db / Bb, with pulsing bass and stereo arpeggios.
    roots=[39,35,37,34]
    for bar in range(math.ceil(duration/(4*BEAT))):
        at=bar*4*BEAT;root=roots[(bar//2)%4]
        intervals=[0,3,7] if (bar//2)%4 in [0,3] else [0,4,7]
        for j in range(8):
            b=bar*4+j*.5
            if b>=496:continue
            gain=.12 if 240<=b<272 else .24
            add(at+j*.5*BEAT,tone(root+(12 if j%4==3 else 0),BEAT*.42,'bass'),gain)
            note=root+24+intervals[j%3]+(12 if j%4==3 else 0)
            add(at+j*.5*BEAT,tone(note,BEAT*.65,'bell'),.075,(-1)**j*.6)
        for semitone in intervals:
            add(at,tone(root+12+semitone,4*BEAT,'pad'),.075, (semitone-3)/12)
    # Intro and interlude use the lead's contour on a bell; verses alternate with choruses.
    for phrase in range(63):
        beat=phrase*8
        chorus=(64<=beat<128 or 192<=beat<240 or 304<=beat<368 or 400<=beat<480)
        melody=(CHORUS if chorus else VERSE)[phrase%4]
        pos=beat*BEAT
        for semi,eighths in melody:
            length=eighths*.5*BEAT
            if beat<16 or 240<=beat<272 or beat>=480:
                voice='bell';gain=.19
            else:voice='lead';gain=.20 if chorus else .18
            note=63+semi
            sig=tone(note,length*.92+.02,voice)
            add(pos,sig,gain)
            add(pos+BEAT*.75,sig,gain*.17,-.5)
            add(pos+BEAT*1.5,sig,gain*.08,.5)
            if chorus:add(pos,tone(note-12,length*.9,'lead'),.055,.15)
            pos+=length
    # Gentle bus saturation, bounded peaks, and clean fades.
    mix=np.tanh(mix*1.15)
    mix*=.92/max(.92,float(np.max(np.abs(mix))))
    fade=min(n,int(2.5*sr));mix[-fade:]*=np.linspace(1,0,fade)[:,None]
    mix[:int(sr*.05)]*=np.linspace(0,1,int(sr*.05))[:,None]
    with wave.open(str(path),'wb') as w:
        w.setnchannels(2);w.setsampwidth(2);w.setframerate(sr)
        w.writeframes((mix*32767).astype('<i2').tobytes())
    return {'sample_rate':sr,'peak':float(np.max(np.abs(mix))),'rms':float(np.sqrt(np.mean(mix**2)))}


def contact_sheet(path):
    thumb=(320,240);sheet=Image.new('RGB',(thumb[0]*5,270*7),(35,35,35))
    d=ImageDraw.Draw(sheet)
    for i,(_,name) in enumerate(SHOTS):
        t=float(STARTS[i]+(STARTS[i+1]-STARTS[i])*.43)
        im=frame(t,(640,480)).resize(thumb,Image.Resampling.LANCZOS)
        x=(i%5)*320;y=(i//5)*270
        sheet.paste(im,(x,y))
        d.text((x+8,y+247),f'{i+1:02}  {int(t)//60}:{int(t)%60:02}  {name}',fill='white')
    sheet.save(path)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--width',type=int,default=960)
    p.add_argument('--fps',type=int,default=30)
    p.add_argument('--duration',type=float,default=DURATION)
    p.add_argument('--sheet-only',action='store_true')
    p.add_argument('--output',type=Path,default=OUT/'bad-apple-from-memory.mp4')
    args=p.parse_args()
    if args.width%8 or args.width<160:p.error('width must be a multiple of 8 and at least 160')
    if args.fps<1 or not 0<args.duration<=DURATION:p.error('invalid fps or duration')
    OUT.mkdir(exist_ok=True);args.output.parent.mkdir(parents=True,exist_ok=True)
    contact_sheet(OUT/'storyboard.jpg')
    if args.sheet_only:return
    duration=math.ceil(args.duration*args.fps)/args.fps
    audio_path=args.output.with_suffix('.wav')
    stats=soundtrack(audio_path,duration)
    w=args.width;h=w*3//4
    cmd=['ffmpeg','-hide_banner','-loglevel','warning','-y','-f','rawvideo','-pix_fmt','gray','-s',f'{w}x{h}','-r',str(args.fps),'-i','pipe:0','-i',str(audio_path),'-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart','-t',str(duration),'-metadata','title=Bad Apple — From Memory','-metadata','comment=Procedural memory reconstruction; no reference footage, recordings, or images used.',str(args.output)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for i in range(round(duration*args.fps)):
            # Draw at 4/3 output size, then antialias down to the final frame.
            im=frame(i/args.fps,(w*4//3,h*4//3)).resize((w,h),Image.Resampling.LANCZOS)
            proc.stdin.write(im.tobytes())
            if i%(args.fps*10)==0: print(f'{i/args.fps:6.1f} / {duration:.1f} seconds',flush=True)
    finally:
        proc.stdin.close()
    if proc.wait():raise RuntimeError('FFmpeg encoding failed')
    report={'duration_seconds':duration,'width':w,'height':h,'fps':args.fps,'shots':len(SHOTS),'audio':stats,'source':'memory only; procedural geometry and synthesized instrumental'}
    args.output.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'Finished: {args.output}',flush=True)

if __name__=='__main__':main()

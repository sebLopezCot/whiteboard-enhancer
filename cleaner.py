# Algorithms used in this script were inspired by the following paper
# http://research.microsoft.com/en-us/um/people/zhang/Papers/TR03-39.pdf
# Whiteboard Scanning and Image Enhancement
# by Zhengyou Zhang, Li-wei He
# from June 2003


from PIL import Image
from pylab import *
import time
import heapq
import math
import sys

import fitting

class Timer:
    def __init__(self):
        self.timer = 0

    def start(self):
        self.timer = time.time()

    def getAndReset(self):
        temp = time.time() - self.timer
        self.timer = time.time()
        return temp

timer = Timer()

def lum(pixel):
    R,G,B = pixel
    return 0.2126*R + 0.7152*G + 0.0722*B

def below255(val):
    return 255 if val > 255 else val

timer.start()

print 'Loading image...'

# m_img_path = 'board1.jpg'
m_img_path = 'bad_whiteboard_small_res_focus.jpg'

if len(sys.argv) > 1:
    m_img_path = sys.argv[1]

image = Image.open(m_img_path).convert('RGB')
im = array(image)

print 'took', timer.getAndReset(), 'seconds.'

print 'Performing setup...'
# image properties
height = len(im)
width = len(im[0])

# calculate the whiteboard image
boxwidth = boxheight = 10
max_wb_im_dim = 150
size = ()
if width > height:
    size = (max_wb_im_dim,int(1.0 * max_wb_im_dim / width * height))
else:
    size = (int(1.0 * max_wb_im_dim / height * width), max_wb_im_dim)

smaller_im = array(image.resize(size))

smaller_h = len(smaller_im)
smaller_w = len(smaller_im[0])

wb_im = array(smaller_im)

print 'took', timer.getAndReset(), 'seconds.'

print 'Calculating whiteboard image...'

profile_sum = 0
num_profiles = 0
queTimer = Timer()
queTimer.start()

points_to_fit = [] # for fitting to rgb colorspace

for rbox in range(0, smaller_h/boxheight): # need to add the +1 in later for the pixels that end up not fitting in the box
    for cbox in range(0, smaller_w/boxwidth):
        # grab the box of pixels
        box = [[smaller_im[r][c] for c in range(cbox*boxwidth, (cbox+1)*boxwidth)] for r in range(rbox*boxheight, (rbox+1)*boxheight)]

        queTimer.getAndReset()

        # store each RGB pixel color in a max heap based on luminosity value and pull out the top 25%
        heap = []
        for y in range(0, boxheight):
            for x in range(0, boxwidth):
                heapq.heappush(heap, (255 - lum(box[y][x]), (box[y][x][0], box[y][x][1], box[y][x][2]) ))

        n = int((boxwidth*boxheight)*0.25)
        topcolors = [heapq.heappop(heap)[1] for i in range(0, n)]

        # average these top 25% colors in RGB
        r = sum([topcolors[i][0] for i in range(0,n)]) / n
        g = sum([topcolors[i][1] for i in range(0,n)]) / n
        b = sum([topcolors[i][2] for i in range(0,n)]) / n

        color_wb = (r,g,b)
        points_to_fit.append(((0.5+cbox)*boxwidth, (0.5+rbox)*boxheight, lum(color_wb)))

        # may be able to reduce time by only saving into a rbox by cbox sized array of color vals
        for r in range(rbox*boxheight, (rbox+1)*boxheight):
            for c in range(cbox*boxwidth, (cbox+1)*boxwidth):
                wb_im[r][c] = color_wb

        profile_sum += queTimer.getAndReset()
        num_profiles += 1


fit_func = fitting.fit(points_to_fit)

max_val = 0
min_val = 255

for r in range(smaller_h):
    for c in range(smaller_w):
        wb_im[r][c] = [int(fit_func(c,r))] * 3
        if wb_im[r][c][0] > max_val:
            max_val = wb_im[r][c][0]

wb_im = array(Image.fromarray(wb_im).resize((width, height)))

figure()
imshow(wb_im)
figure()
imshow(im)
show()

print 'took', timer.getAndReset(), 'seconds.'

print 'with average queue building time of ', profile_sum / num_profiles

""" need to eventually do step 3 which is "Filter the colors of the cells by locally fitting a plane in the RGB
space. Occasionally there are cells that are entirely covered by pen strokes, the cell color computed in
Step 2 is consequently incorrect. Those colors are rejected as outliers by the locally fitted plane and are
replaced by the interpolated values from its neighbors" """

print 'Uniform whitening...'

# make the background uniformly white
pen_im = [[False for j in range(0, width)] for i in range(0, height)]
for r in range(0, height):
    for c in range(0, width):
        im[r][c][0] = im[r][c][0]*1.0/wb_im[r][c][0] * 255 if im[r][c][0] < wb_im[r][c][0] else 255
        im[r][c][1] = im[r][c][1]*1.0/wb_im[r][c][1] * 255 if im[r][c][1] < wb_im[r][c][1] else 255
        im[r][c][2] = im[r][c][2]*1.0/wb_im[r][c][2] * 255 if im[r][c][2] < wb_im[r][c][2] else 255

print 'took', timer.getAndReset(), 'seconds.'

print 'Pen saturation...'

# reduce image noise and increase color saturation of the pen strokes
p = 1.0
for r in range(0, height):
    for c in range(0, width):
        im[r][c] = [im[r][c][n] * 0.5 * (1.0 - cos(math.pi * (im[r][c][n]/255.0)**p)) for n in range(0, len(im[r][c]))]

print 'took', timer.getAndReset(), 'seconds.'


imshow(im)

print 'Showing image...'

show()

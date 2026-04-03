import cv2
import mediapipe as mp
import pyautogui
import time, math
# -------- One Euro Filter (for smooth & accurate cursor) --------
class LowPass:
def init (self): self.s = None
def filter(self, x, a):
if self.s is None: self.s = x
self.s = a * x + (1 - a) * self.s
return self.s
def alpha from cutoff(cutoff, dt):
if cutoff <= 0: return 1.0
tau = 1.0 / (2.0 * math.pi * cutoff)
return 1.0 / (1.0 + tau / max(dt, 1e-6))
class OneEuro2D:
def init (self, min cutoff=1.3, beta=0.02, d cutoff=1.0):
self.min cutoff = min cutoff
self.beta = beta
self.d cutoff = d cutoff
self. xf = LowPass(); self. yf = LowPass()
self. dfx = LowPass(); self. dfy = LowPass()
self. last = None
def filter(self, x, y, dt):
if self. last is None:
dx, dy = 0.0, 0.0
else:
dx = (x - self. last[0]) / dt
dy = (y - self. last[1]) / dt
ad = alpha from cutoff(self.d cutoff, dt)
edx = self. dfx.filter(dx, ad)
edy = self. dfy.filter(dy, ad)
cx = self.min cutoff + self.beta * abs(edx)
cy = self.min cutoff + self.beta * abs(edy)
ax = alpha from cutoff(cx, dt)
ay = alpha from cutoff(cy, dt)
fx = self. xf.filter(x, ax)
fy = self. yf.filter(y, ay)
self. last = (fx, fy)
return fx, fy
# ------------------ Config ------------------
PINCH TH PX = 40 # Left click threshold
PINCH TH PX R = 45 # Right click threshold
DEADZONE PX = 2
SCROLL GAIN = 1600
ZOOM GAIN = 1800
DOUBLE CLICK INTERVAL = 0.4 # seconds
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0
# ------------------ Init ------------------
mp hands = mp.solutions.hands
hands = mp hands.Hands(min detection confidence=0.7,
min tracking confidence=0.7,
max num hands=1)
mp draw = mp.solutions.drawing utils
screen w, screen h = pyautogui.size()
cap = cv2.VideoCapture(0)
eu = OneEuro2D(min cutoff=1.3, beta=0.03, d cutoff=1.5)
t prev = time.time()
# Gesture flags
left clicked = False
right clicked = False
scroll prev y = None
zoom prev y = None
last pinch time = 0
click ready = True
def dist px(a, b, w, h):
return math.hypot((a.x - b.x) * w, (a.y - b.y) * h)
def fingers up(lm, handed='Right'):
TIP = { 'thumb':4, 'index':8, 'middle':12, 'ring':16, 'pinky':20 }
PIP = { 'thumb':3, 'index':6, 'middle':10, 'ring':14, 'pinky':18 }
up = {}
thumb tip = lm.landmark[TIP['thumb']]
thumb ip = lm.landmark[PIP['thumb']]
if handed == 'Right':
up['thumb'] = thumb tip.x > thumb ip.x
else:
up['thumb'] = thumb tip.x < thumb ip.x
for f in ['index','middle','ring','pinky']:
tip = lm.landmark[TIP[f]]
pip = lm.landmark[PIP[f]]
up[f] = tip.y < pip.y
return up
while cap.isOpened():
ok, frame = cap.read()
if not ok: break
frame = cv2.flip(frame, 1)
h, w, = frame.shape
rgb = cv2.cvtColor(frame, cv2.COLOR BGR2RGB)
res = hands.process(rgb)
now = time.time()
dt = max(now - t prev, 1e-3)
t prev = now
if res.multi hand landmarks:
lm = res.multi hand landmarks[0]
handed = 'Right'
if res.multi handedness:
handed = res.multi handedness[0].classification[0].label
idx = lm.landmark[mp hands.HandLandmark.INDEX FINGER TIP]
mid = lm.landmark[mp hands.HandLandmark.MIDDLE FINGER TIP]
ring = lm.landmark[mp hands.HandLandmark.RING FINGER TIP]
thumb = lm.landmark[mp hands.HandLandmark.THUMB TIP]
# Cursor position (filtered)
cx = int(idx.x * screen w)
cy = int(idx.y * screen h)fx, fy = eu.filter(cx, cy, dt)
fx = int(max(0, min(screen w - 1, fx)))
fy = int(max(0, min(screen h - 1, fy)))
mx, my = pyautogui.position()
if abs(fx - mx) > DEADZONE PX or abs(fy - my) > DEADZONE PX:
pyautogui.moveTo(fx, fy)
# Distances in pixels
d idx = dist px(idx, thumb, w, h)
d mid = dist px(mid, thumb, w, h)
d ring = dist px(ring, thumb, w, h)
ups = fingers up(lm, handed)
# ----- Zoom Mode -----
if d ring < PINCH TH PX:
y now = ring.y * h
if zoom prev y is not None:
dy = y now - zoom prev y
if abs(dy) > 1.0:
pyautogui.keyDown('ctrl')
pyautogui.scroll(int(-dy * (ZOOM GAIN / h)))
pyautogui.keyUp('ctrl')
zoom prev y = y now
else:
zoom prev y = None
# ----- LEFT CLICK / DOUBLE CLICK -----
if d idx < PINCH TH PX and click ready:
now time = time.time()
if now time - last pinch time < DOUBLE CLICK INTERVAL:
pyautogui.doubleClick()
last pinch time = 0
else:
pyautogui.click()
last pinch time = now time
click ready = False
if d idx >= PINCH TH PX + 10:
click ready = True # Reset when fingers separate
# ----- RIGHT CLICK -----
if d mid < PINCH TH PX R and not right clicked:
pyautogui.rightClick()
right clicked = True
if d mid >= PINCH TH PX R + 10:
right clicked = False
# ----- SCROLL -----
if ups['index'] and ups['middle'] and d idx >= PINCH TH PX and d mid
>= PINCH TH PX:
y now = (idx.y + mid.y) * 0.5 * h
if scroll prev y is not None:
dy = y now - scroll prev y
if abs(dy) > 1.0:
pyautogui.scroll(int(-dy * (SCROLL GAIN / h)))
scroll prev y = y now
else:
scroll prev y = None
mp draw.draw landmarks(frame, lm, mp hands.HAND CONNECTIONS)
cv2.imshow(”Hand Gesture Control”, frame)
key = cv2.waitKey(1)
if key & 0xFF == ord('q'):
break
cap.release()
cv2.destroyAllWindows()
 
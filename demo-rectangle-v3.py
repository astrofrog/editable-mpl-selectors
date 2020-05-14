import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


RECTANGLE_ANCHOR_LOCS = [(-1, -1), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0)]
ANCHOR_SIZE = 10

class EditableRectangle:

    _angle = 0

    def __init__(self, ax):
        self.ax = ax

        # Set up main rectangle
        self.rect = Rectangle((0, 0), 0, 0, visible=False, transform=None, picker=True)
        self.ax.add_patch(self.rect)

        # Set up anchors
        self.anchors = []
        for i in range(len(RECTANGLE_ANCHOR_LOCS)):
            anchor = Rectangle((0, 0), ANCHOR_SIZE, ANCHOR_SIZE, visible=False, transform=None, facecolor='red', picker=True)
            self.anchors.append(anchor)
            self.ax.add_patch(anchor)

        self.press = None
        self.mode = None
        self.connect()

    def connect(self):
        self.cid_press = self.ax.figure.canvas.mpl_connect('button_press_event', self.on_press)
        self.cid_release = self.ax.figure.canvas.mpl_connect('button_release_event', self.on_release)
        self.cid_motion = self.ax.figure.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.cid_pick = self.ax.figure.canvas.mpl_connect('pick_event', self.on_pick)

    def on_pick(self, event):
        if event.artist in self.anchors:
            if event.mouseevent.key == 'r':
                self.mode = 'anchor-rotate'
                self.center_x = self.x0 + self.width * 0.5
                self.center_y = self.y0 + self.height * 0.5
                self.angle_start = self.angle
                self.angle_drag_start = np.degrees(np.arctan2(event.mouseevent.y - self.center_y, event.mouseevent.x - self.center_x))
                print(self.angle_start)
            else:
                self.mode = 'anchor-drag'
                anchor_index = self.anchors.index(event.artist)
                self.active_anchor_index = anchor_index
            self.press = True
        elif event.artist is self.rect:
            self.mode = 'rectangle-drag'
            self.drag_start_x0 = self.x0
            self.drag_start_y0 = self.y0
            self.drag_start_x = event.mouseevent.x
            self.drag_start_y = event.mouseevent.y
            self.press = True

    def on_press(self, event):

        if event.inaxes != self.ax:
            return

        if self.mode == 'create':
            self.x0 = event.x
            self.y0 = event.y
            self.rect.set_visible(True)
            self.press = True

        # contains, attrd = self.rect.contains(event)
        # if not contains: return
        # print('event contains', self.rect.xy)
        # x0, y0 = self.rect.xy
        # self.press = x0, y0, event.x, event.y

    @property
    def angle(self):
        return self._angle

    @angle.setter
    def angle(self, value):
        self._angle = value
        self.rect.angle = value
        self.rect._update_patch_transform()

    @property
    def x0(self):
        return self.rect.get_x()

    @x0.setter
    def x0(self, value):
        self.rect.set_x(value)

    @property
    def y0(self):
        return self.rect.get_y()

    @y0.setter
    def y0(self, value):
        self.rect.set_y(value)

    @property
    def width(self):
        return self.rect.get_width()

    @width.setter
    def width(self, value):
        self.rect.set_width(value)

    @property
    def height(self):
        return self.rect.get_height()

    @height.setter
    def height(self, value):
        self.rect.set_height(value)

    def on_motion(self, event):

        if self.press is None:
            return

        if event.inaxes != self.ax:
            return

        if self.mode == 'create':

            self.width = event.x - self.x0
            self.height = event.y - self.y0

            self.rect.figure.canvas.draw()

        elif self.mode == 'rectangle-drag':

            self.x0 = self.drag_start_x0 + event.x - self.drag_start_x
            self.y0 = self.drag_start_y0 + event.y - self.drag_start_y

            self.update_anchors()

            self.rect.figure.canvas.draw()

        elif self.mode == 'anchor-drag':

            px, py = RECTANGLE_ANCHOR_LOCS[self.active_anchor_index]

            if px == -1:
                self.x0, self.width = event.x, self.x0 + self.width - event.x
            elif px == 1:
                self.width = event.x - self.x0

            if py == -1:
                self.y0, self.height = event.y, self.y0 + self.height - event.y
            elif py == 1:
                self.height = event.y - self.y0

            self.update_anchors()

            self.rect.figure.canvas.draw()

        elif self.mode == 'anchor-rotate':

            angle_current = np.degrees(np.arctan2(event.y - self.center_y, event.x - self.center_x))

            self.angle = self.angle_start + (angle_current - self.angle_drag_start)

            self.update_anchors()

            self.rect.figure.canvas.draw()

    def on_release(self, event):
        if self.mode == 'create':
            self.update_anchors()
            self.set_anchor_visibility(True)
        self.press = None
        self.mode = None
        self.rect.figure.canvas.draw()

    def set_anchor_visibility(self, visible):
        for anchor in self.anchors:
            anchor.set_visible(visible)

    def update_anchors(self):
        for anchor, (dx, dy) in zip(self.anchors, RECTANGLE_ANCHOR_LOCS):
            xc = self.x0 + 0.5 * self.width
            yc = self.y0 + 0.5 * self.height
            dx = 0.5 * (dx * self.width - ANCHOR_SIZE)
            dy = 0.5 * (dy * self.height - ANCHOR_SIZE)
            dxr = dx * np.cos(np.radians(self.angle)) - dy * np.sin(np.radians(self.angle))
            dyr = dx * np.sin(np.radians(self.angle)) + dy * np.cos(np.radians(self.angle))
            anchor.set_xy((xc + dxr, yc + dyr))

    def disconnect(self):
        self.ax.figure.canvas.mpl_disconnect(self.cid_press)
        self.ax.figure.canvas.mpl_disconnect(self.cid_release)
        self.ax.figure.canvas.mpl_disconnect(self.cid_motion)


if __name__ == "__main__":

    fig = plt.figure()
    ax = fig.add_subplot(111)
    rect = EditableRectangle(ax)
    rect.mode = 'create'
    plt.show()


import cv2
# import matplotlib.pyplot as plt
# for field, roi in rois.items():
#     plt.imshow(roi, cmap='gray')
#     plt.title(field)
#     plt.show()


drawing = False  # true if mouse is pressed
ix, iy = -1, -1
rect = None  # selected rectangle coords

def draw_rectangle(event, x, y, flags, param):
    global ix, iy, drawing, rect, img_copy

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix, iy = x, y
        rect = None

    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            img_copy = img.copy()
            cv2.rectangle(img_copy, (ix, iy), (x, y), (0, 255, 0), 2)
            cv2.imshow("Image", img_copy)

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        rect = (min(ix, x), min(iy, y), abs(x - ix), abs(y - iy))
        print(f"Selected rectangle: x={rect[0]}, y={rect[1]}, w={rect[2]}, h={rect[3]}")
        cv2.rectangle(img, (rect[0], rect[1]), (rect[0]+rect[2], rect[1]+rect[3]), (0, 255, 0), 2)
        cv2.imshow("Image", img)

# image_path = "uploads/ktp_20250701_115038.jpg"
image_path = "proktpori.jpg"
img = cv2.imread(image_path)
img_copy = img.copy()
cv2.namedWindow("Image")
cv2.setMouseCallback("Image", draw_rectangle)

print("Drag mouse to select area. Press 'q' to quit.")

while True:
    cv2.imshow("Image", img)
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break

cv2.destroyAllWindows()

if rect:
    x, y, w, h = rect
    print(f"Final selected area -> x: {x}, y: {y}, width: {w}, height: {h}")
else:
    print("No area selected.")

# RUMUS ROIS
# x: 117, y: 81, width: 122, height: 24
# x, y, w, h = 117, 81, 122, 24

# y_start = y

# y_end = y + height

# x_start = x

# x_end = x + width

# "Nama": auto_expand_roi(gray, 81, 81+24, 117, 117+122)
# # yaitu
# "Nama": auto_expand_roi(gray, 81, 105, 117, 239)


# contoh
#  x: 119, y: 84, width: 125, height: 16
# "Nama": auto_expand_roi(gray, 84, 84+16, 119, 119+125)


#  x: 119, y: 45, width: 222, height: 24
# "Nama": auto_expand_roi(gray, 45, 45+24, 119, 119+222)

# x: 346, y: 134, width: 619, height: 61
# "Nama": auto_expand_roi(gray, 134, 134+61, 346, 346+619)
# -*- coding: utf-8 -*-
"""Preprocessing

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1QRiY-Xj5UuwfYsAUSsQHTunuHJGfJ9fE
"""

#Authors - Thomas Bardhi and Joe Wang
import os
import cv2
import tifffile as tiff
import matplotlib.pyplot as plt
from scipy import ndimage as ndi
from skimage.feature import peak_local_max
from skimage.segmentation import watershed
from skimage.color import label2rgb
import numpy as np

def read_image(file_path):
    image = tiff.imread(file_path)
    return image

def segment_image(image_path):
    # Load image
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(image, (5, 5), 0)

    # Use Adaptive Thresholding
    thresholded = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 35, 10)

    # Morphological operations to remove small noise - opening
    # To remove holes we can use closing
    kernel = np.ones((3,3), np.uint8)
    opened = cv2.morphologyEx(thresholded, cv2.MORPH_OPEN, kernel, iterations=2)

    # We sure background is black so we dilate it
    sure_bg = cv2.dilate(opened, kernel, iterations=3)

    # Compute the distance transform
    distance_transform = cv2.distanceTransform(opened, cv2.DIST_L2, 5)
    
    # Let's threshold the dist transform by starting at 1/2 its max value.
    _, sure_fg = cv2.threshold(distance_transform, 0.5*distance_transform.max(), 255, 0)

    # Subtract the sure foreground from sure background
    sure_fg = np.uint8(sure_fg)
    unknown = cv2.subtract(sure_bg, sure_fg)

    # Marker labelling
    _, markers = cv2.connectedComponents(sure_fg)

    # Add one to all labels so that sure background is not 0, but 1
    markers = markers+1

    # Now, mark the region of unknown with zero
    markers[unknown==255] = 0

    # Apply the watershed algorithm
    markers = cv2.watershed(cv2.cvtColor(image, cv2.COLOR_GRAY2RGB), markers)

    return markers-1

def save_images(segmented_image, output_path, image_name):
    # Convert image data to uint8 format if necessary
    if segmented_image.dtype != 'uint8':
        segmented_image = (segmented_image * 255).astype('uint8')

    # Save the original and segmented images as TIFF files
    tiff.imwrite(os.path.join(output_path, f'segmented_{image_name}'), segmented_image)


def process_images(image_dir, output_dir):
    image_files = os.listdir(image_dir)

    for image_file in image_files:
        if image_file.endswith('.tif'):
            image_path = os.path.join(image_dir, image_file)
            image = read_image(image_path)
            image = image[1, :, :]
            segmented_image = segment_image(image_path)
            save_images(segmented_image, output_dir, image_file)
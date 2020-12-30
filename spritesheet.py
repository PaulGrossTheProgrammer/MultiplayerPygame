# Helper module for managing lists of images
# Includes loading sets of images from files,
# and rotating sets of images.

import math
import pygame

class Spritesheet():
    def __init__(self, cols, rows, filename=None, image=None,
                 rect=None, scale=None, alpha_color=None):
        # Either a filename or image argument must be supplied
        # If the optional rect argument is supplied,
        # only that rectangular portion of the image is used
        if filename is None and image is None:
            raise RuntimeError("filename= or image= must be given")
        if filename is not None and image is not None:
            raise RuntimeError("Cannot use both filename= and image=")

        if filename is not None:
            self.sheet_image = pygame.image.load(filename)
        else:
            self.sheet_image = image

        # FIXME - alpha doesn't seem to work with convert(),
        # but convert requires the screen to be initialied
        if alpha_color is not None:
            # self.sheet_image.convert()
            self.sheet_image.set_colorkey(alpha_color)

        if rect is not None:
            self.sheet_image = self.sheet_image.subsurface(rect)

        if scale is not None and scale != 1.0:
            # rows and cols
            new_width = int(scale * self.sheet_image.get_width())
            new_height = int(scale * self.sheet_image.get_height())

            div_rows = new_height//rows
            new_height = rows * div_rows
            div_cols = new_width//rows
            new_width = cols * div_cols

            self.sheet_image = pygame.transform.scale(
                    self.sheet_image, (new_width, new_height))

        self.cols = cols
        self.rows = rows
        self.frame_x = self.sheet_image.get_width() // self.cols
        self.frame_y = self.sheet_image.get_height() // self.rows

    def draw(self, surface, position=[0, 0]):
        surface.blit(self.sheet_image, position)
        # TODO - blit the rotated image lists too, at the bottom

    def get_frames(self, start_frame=0, end_frame=None):
        # By default all the frames in the spritesheet are loaded,
        # from starting from left to right, top to bottom
        # specify start_frame and end_frame to use less of the sheet
        # end_frame=None means load up to the last frame
        # end_frame is inclusive
        if end_frame is None or end_frame > self.cols * self.rows:
            end_frame = self.cols * self.rows - 1

        frame_list = []
        curr_frame = 0
        curr_x = 0
        curr_y = 0
        while curr_frame <= end_frame:
            if curr_frame >= start_frame:
                # Point to a subsurface of the spritesheet
                sub_rectangle = pygame.Rect((curr_x, curr_y),
                                            (self.frame_x, self.frame_y))
                new_image = self.sheet_image.subsurface(sub_rectangle)
                frame_list.append(new_image)

            curr_x += self.frame_x
            if curr_x >= self.sheet_image.get_width():
                curr_x = 0
                curr_y += self.frame_y

            curr_frame += 1

        return frame_list

    def get_frames_in_row(self, row, start_frame=0, end_frame=None):
        # By default all the frames in the row are loaded
        # specify start_frame and end_frame to use less of the sheet
        # end_frame=None means load up to the last frame in the row
        # end_frame is inclusive
        if end_frame is None or end_frame >= self.cols:
            end_frame = self.cols - 1

        frame_list = []
        curr_frame = 0
        curr_x = 0
        curr_y = row * self.frame_y
        while curr_frame <= end_frame:
            if curr_frame >= start_frame:
                # Point to a subsurface of the spritesheet
                sub_rectangle = pygame.Rect((curr_x, curr_y),
                                            (self.frame_x, self.frame_y))
                new_image = self.sheet_image.subsurface(sub_rectangle)
                frame_list.append(new_image)

            curr_x += self.frame_x
            curr_frame += 1

        return frame_list

    def create_angled_image_lists(self, image_list, divisions, name=""):
        # Create a list of lists of rotated images from the image list
        # by dividing the full circle into evenly spaced divisions.
        # Each index in the list is a rotated list of the original images,
        # Corresponding to an angle division.
        # The list can optionally be given a name, which can be used by
        # TODO get_rotated_image_set(name="SOME_NAME")
        self.all_angles = []

        angle_step = 2*math.pi/divisions
        angle_curr = 0
        while angle_curr < 2 * math.pi:
            if angle_curr == 0:
                rotated_images = image_list  # Preserve originals as zero angle
            else:
                rotated_images = []
                # Fix for pygame transform using -(degrees) instead of radians
                pygame_angle_rotate = -(180/math.pi * angle_curr)

                self.angle_frames = []
                for image in image_list:
                    image = pygame.transform.rotate(image, pygame_angle_rotate)
                    rotated_images.append(image)

            self.all_angles.append(rotated_images)
            angle_curr += angle_step

    def get_angled_image_list(self, angle, name=""):
        # TODO - make sure create_rotated_image_sets() has already been called
        # TODO get_rotated_image_set(name="SOME_NAME")

        angle_half_step = math.pi/len(self.all_angles)
        angle -= angle_half_step
        if angle < 0:
            angle += 2*math.pi

        ratio = angle/(2*math.pi)
        index = ratio * len(self.all_angles)
        index = int(index) + 1

        while index >= len(self.all_angles):
            index -= len(self.all_angles)

        return self.all_angles[index]
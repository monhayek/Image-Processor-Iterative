"""Image processing module for OCR.
 
This module contains the necessary methods to process Image files of
arbitrary sizes before sending to the Vision API.
"""
from __future__ import division
 
import io
import math
import os
import uuid
 
from PIL import Image
 
from google.cloud import storage
from google.cloud import vision
 
 
self.vision_client = vision.ImageAnnotatorClient()
self.storage_client = storage.Client()
 
 
def image_divider(uri, overlap=0.25):
  """Gets Vision API response from Images files of arbitrary sizes.
 
  This function takes in an image uri and a customizable overlap percent.
  If the image < 20 MB, it sends it to Vision API. If the
  file size > 20MB, it divides it into sub-images and adjusts the traversing
  step size using the desired overlap percentage.
 
  Args:
    uri: 'https://i.stack.imgur.com/WiDpa.jpg'.
    overlap: Desired percentage of overlap between the sub images.
 
  Returns:
    Vision API response for all sub images.
    #TODO: Implement horizontal division function.
  """
  if not uri:
    raise ValueError('No URI was given.')
 
  folder_name = 'tmp/' + str(uuid.uuid4())
  original_file = folder_name + '/original'
  os.mkdir(folder_name)
 
  with open(original_file, 'w') as file_obj:
    storage_client.download_blob_to_file(uri, file_obj)
  file_size = os.path.getsize(original_file)
  print file_size
  max_size_bytes = 20 * 1024 * 1024
  if file_size > max_size_bytes:
    im = Image.open(original_file)
    width, height = im.size
 
    print im.size
    factor = int(file_size / max_size_bytes)
 
    x_block_size = int(width / factor)
    y_block_size = int(height / factor)
    x_step_size = int((1-overlap) * x_block_size)
    y_step_size = int((1-overlap) * y_block_size)
 
    final_response = []
    #TODO(): Can't be an array, implement merge function
 
    for x_block in range(int(math.ceil((width - x_block_size + x_step_size)
                                       / x_step_size))):
      for y_block in range(int(math.ceil((height - y_block_size + y_step_size)
                                         / y_step_size))):
        print (x_block * x_step_size,
               x_block * x_step_size,
               y_block * y_step_size,
               x_block * x_step_size + x_block_size,
               y_block * y_step_size + y_block_size,
               '{}_{}.jpg'.format(x_block, y_block))
 
        sub_image = im.crop((x_block * x_step_size,
                             y_block * y_step_size,
                             x_block * x_step_size + x_block_size,
                             y_block * y_step_size + y_block_size))
 
        output_file = 'tmp/{}_{}.jpg'.format(x_block, y_block)
        sub_image.save(output_file)
        with io.open(output_file, 'rb') as image_file:
          content = image_file.read()
        image = vision.types.Image(content=content)
        response = vision_client.document_text_detection(image=image)
        if response.error.code:
          raise Exception('Something went wrong with the Vision API:' +
                          str(response.error))
        if not response.full_text_annotation.pages: continue
        final_response.append(response.full_text_annotation.pages[0])
    return final_response
 
  else:
    image = vision.types.Image()
    image.source.image_uri = uri
 
    response = vision_client.document_text_detection(image=image)
    if response.error.code:
      raise Exception('Something went wrong with the Vision API:' +
                      str(response.error))
    if not response.full_text_annotation.pages:
      return None
  return [response.full_text_annotation.pages[0]]

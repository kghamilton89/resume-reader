# -*- coding: utf-8 -*-
"""
Created on Wed Dec 22 02:48:47 2021

@author: davba

path to this file rn D:\ResumeIT\full_pipeline.py
python -m streamlit run D:\ResumeIT\full_pipeline.py

"""
import streamlit as st #framework 
import pdf2image #converts pdf
from pdf2image import convert_from_path 
import easyocr
import numpy as np
import PIL # Python Imaging Library
from PIL import ImageDraw # drawing bounding boxes
import tensorflow as tf
from IPython.display import display,Image
from matplotlib.pyplot import imshow
import xml.dom.minidom
import pandas as pd
import mrcnn
import mrcnn.utils
import mrcnn.config
import mrcnn.model
import mrcnn.visualize
import urllib.request
import os
import xml.etree
import cv2

@st.cache
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode('utf-8')

def run_model(img_array):
    CLASS_NAMES = ['BG', 'Personal Info', 'Education', 'Skills', 'Projects', 'Work Experience', 'Extra']
    
    class SimpleConfig(mrcnn.config.Config):
        NAME = "coco_inference"
        
        GPU_COUNT = 1
        IMAGES_PER_GPU = 1
    
        NUM_CLASSES = len(CLASS_NAMES)
    
    model = mrcnn.model.MaskRCNN(mode="inference", 
                                 config=SimpleConfig(),
                                 model_dir=os.getcwd())
    
    model.load_weights(filepath=r'D:\\ResumeIT\\RESUMEIT_Model_Finalized.h5', 
                       by_name=True)
    
    class_dict = {'bg' : 0, 
                  'Personal Info' : 1, 
                  'Education' : 2,
                  'Skills' : 3,
                  'Projects' : 4,
                  'Work Experience' : 5,
                  'Extra' : 6
                }
    
    inv_class_dict = {0:'bg', 
                  1:'Personal Info', 
                  2:'Education',
                  3:'Skills',
                  4:'Projects',
                  5:'Work Experience',
                  6: 'Extra'
                }
    
    sections = ['Personal Info', 'Education', 'Skills', 'Projects', 'Work Experience', 'Extra']
    extracted_info_df = pd.DataFrame(columns=sections)
    
    #Assuming an array of images in cv2 format: img_array
    for image in img_array:
        
        pred = model.detect([image], verbose=0)
        pred = pred[0]
        #The bnd box outputed is [y1,x1,y2,x2]
        
        full_info = list()
        class_list = list()
        for i in range(len(pred['rois'])):
            img_pil = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            temp_img = PIL.Image.fromarray(img_pil)
            current_bnd_box = pred['rois'][i]
            current_box_class = pred['class_ids'][i]
            #pil_img.crop(box=[x1,y1,x2,y2])
            crop_box = [current_bnd_box[1], current_bnd_box[0], current_bnd_box[3], current_bnd_box[2]]
            crop_img = temp_img.crop(crop_box)
            
            #text for this section
            section_text = ""
            bounds = reader.readtext(np.array(crop_img),min_size=0,slope_ths=0.2,ycenter_ths=0.7,height_ths=0.6,width_ths=0.8)
            for b in bounds:
                section_text += " " + b[1]
            full_info.append([section_text])
            class_list.append(inv_class_dict[current_box_class])
            
        add_to_df = dict(zip(class_list,full_info))
        
        for key in sections:
            if key in add_to_df:
                continue 
            else:
                add_to_df[key] = [""]
        
        temp_df = pd.DataFrame.from_dict(add_to_df)
            
        extracted_info_df = extracted_info_df.append(temp_df, ignore_index = True)
    
    return extracted_info_df


st.title("Resume Parsing")
os.environ['KMP_DUPLICATE_LIB_OK']='True'
reader= easyocr.Reader(["en"]) # select language 

image_path ="C:/ResumeParser/tempDirectory/resume_image"
# Get Resume Book and Split Resume

uploaded_file =st.file_uploader("Upload Your Resume Book", type=['pdf'], accept_multiple_files=False, key=None, help=None, on_change=None, args=None, kwargs=None)
if uploaded_file is not None:
  if uploaded_file.type == "application/pdf":
    images = pdf2image.convert_from_bytes(uploaded_file.read(),size=(1700,2200))
    st.subheader("Please select page(s)")
    start = st.number_input('Start with page',min_value =1,max_value=len(images),step=1,key="start_page")
    end =  st.number_input('End with page',min_value=1,max_value=len(images),step=1,key="end_page")
    
    split_button = st.button("Split resume book", key='split_button')
    if split_button:
        for i in range(start-1,end):
            img_index = i
            resume = images[img_index]
            
            image_path = "C:/ResumeParser/tempDirectory/resume_image"
        
            image_name = uploaded_file.name.split(".")[0] + str(img_index+1)
            image_ext = image_name + ".jpg"

            resume.save(f"{image_path}/{image_ext}") #save jpeg
        st.success("Finished splitting the resume. Ready to run!")

#Resume is split and saved as images so now we open that to get the resumes for prediction

files = os.listdir(image_path)
img_array = list()
for name in files:
    image = cv2.imread(image_path + "/" + name)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    img_array.append(image)


run_model_button = st.button("Run the Model", key='run_model_button')


# button "Click here to run the model"
df = pd.DataFrame()
if run_model_button:
    df = run_model(img_array)

st.dataframe(data = df)

#save_filename = st.text_input("Enter the file name for the csv file (Don't forget to include .csv)",key="csv_filename")
#save_button = st.button("Save", key='save_button')

#if save_button:
#  df.to_csv(r'C:\\ResumeParser\\'+filename, index = False)
  
#st.write(df)
#if save_button:
#    f = open(r'C:\\ResumeParser\\'+filename, 'w').write(df.to_csv())
#    f.close()
  
csv = convert_df(df)

st.download_button(
     label="Download data as CSV",
     data=csv,
     mime='text/csv')
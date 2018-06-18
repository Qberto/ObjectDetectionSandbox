
# coding: utf-8

# # Crowd Detection Project - Image Exporter
# 
# This process generates training and testing data for image classification from video feeds given ground-truth data found in a feature class.

# ## Pseudocode
# 
# 1. Import needed modules
# 
# 2. Establish runtime variables
#     - GIS
#     - video root directory
#     - labels feature class
#     - labels FC camera field
#     - labels FC label field
#     - labels FC datetime field
#     
# 3. Create Helper Functions:
#     - Input: label FC record (datetime, label, camera) | Output: video url and timestamp
# 
# 4. Iteration: For each record of the labeled feature class...
#     - Run helper function to determine video url and timestamp
#     - Determine output path
#     - Run export using moviepy

# ### 1. Import needed modules


import arcgis
import moviepy.editor as mpy
import datetime
import os


# ### 2. Establish runtime variables

# - GIS
# - video root directory
# - labels feature class
# - labels FC camera field
# - labels FC label field
# - labels FC datetime field

gis = arcgis.gis.GIS("https://esrifederal.maps.arcgis.com", username="Anieto_esrifederal")


# Make reference to directories and other needed paths
video_root_dir = r"D:\5_Data\Transportation\Cameras\SunTrustPark"
labels_fc = r"D:\3_Sandbox_Projects\1806_CobbCounty_PedestrianDetection\Inputs\S123_Labels.gdb\PedestrianCount"
labels_fc_camera_field = "CameraID"
labels_fc_label_field = "degreesaturation"
labels_fc_datetime_field = "PhotoDateTime"


labels_sdf = arcgis.features.SpatialDataFrame.from_featureclass(labels_fc)


# ### 3. Create Helper Functions


# Input: List of video files with names HHhMMmSSs.avi, datetime object | Output: Video containing the datetime
def get_videopath_and_video_timestamp_from_label_timestamp(camera_dir, datetime_object, debug=False):
    
    # Get list of video files in the camera directory
    video_files = os.listdir(camera_dir)
    
    if debug:
        print("<<<< Debug >>>> ")
        print("\nInputs: ")
        print("\tObservation Date: {0}".format(datetime_object.strftime("%y%m%d")))
        print("\tObservation Time: {0}".format(datetime_object.strftime("%H:%M:%S")))
    
    # For each file in video files...
    for ix, video_file in enumerate(video_files):
        
        video_found = False
    
        # we need a datetime range...
        yymmdd = datetime_object.strftime("%y%m%d")
        start = datetime.datetime.strptime(video_files[ix]+" "+yymmdd, "%Hh%Mm%Ss.avi %y%m%d")
        clip = mpy.VideoFileClip(camera_dir + "\\" + video_files[ix])
        runtime = clip.duration
        clip.reader.close()
        end = start + datetime.timedelta(0, runtime)
        
        in_time_range = start <= datetime_object <= end
        
        if debug:
            print("\nRecording: {0}".format(video_file))
            print("\tCamera Dir: {0}".format(camera_dir))
            print("\tStart: {0}".format(start))
            print("\tRuntime: {0}".format(runtime))
            print("\tEnd: {0}".format(end))
            print("\tIn Range?: {0}".format(in_time_range))
        
        # so we can determine if the current timeslot exists there
        if in_time_range:
            
            # And get the video timestamp
            delta_video_timestamp = datetime_object - start
            
            return video_file, str(delta_video_timestamp)
        
    
    print("\nCould not find the needed timeslot in the video...")
            
    return None, None



# Input: label FC record (datetime, label, camera) | Output: video url and timestamp
def retrieve_video_and_time(camera, 
                            label, 
                            datetime_obj,
                            video_root_dir,
                            debug=False):
    
    # This function relies on a video root directory structure as follows:
    
    # Root_Path
        # yymmdd
            # Camera ID
                # HHhMMmSSs.avi
    
    # Parse out datetime object into needed formats
    yymmdd = datetime_obj.strftime("%y%m%d")
    hh = datetime_obj.strftime("%H")
    mm = datetime_obj.strftime("%M")
    ss = datetime_obj.strftime("%S")
    
    # Determine which video contains the needed time and at which time the label was recorded in the video
    camera_dir = "{0}\\{1}\\{2}".format(video_root_dir, yymmdd, camera)
    video_name, video_time = get_videopath_and_video_timestamp_from_label_timestamp(camera_dir, datetime_obj, debug)
    
    return "{0}\\{1}".format(camera_dir, video_name), video_time


# ### 4.Iteration: For each record of the labeled feature class...
#     - Run helper function to determine video url and timestamp
#     - Determine output path
#     - Run export using moviepy


def main(label_fc, 
         labels_fc_camera_field, 
         labels_fc_label_field, 
         labels_fc_datetime_field, 
         video_root_dir, 
         outputs_dir, 
         debug=False):
    # Convert the labels fc into a spatial dataframe in python memory
    labels_sdf = arcgis.features.SpatialDataFrame.from_featureclass(labels_fc)
    total_observations = labels_sdf.shape[0]
    # Iterate on each record to start the image export
    for index, row in labels_sdf.iterrows():
        
        camera = row[labels_fc_camera_field] 
        label = row[labels_fc_label_field]
        pandas_timestamp = row[labels_fc_datetime_field]
        
        print("\n<<<< Exporting {0} of {1} >>>>".format(index, total_observations))
        print(camera)
        print(label)
        print(pandas_timestamp)
        print("\n")        
        
        # Convert the pandas timestamp to datetime object
        pdt = pandas_timestamp.to_pydatetime()
        # Correct for input data timezone difference
        pdt = pdt - datetime.timedelta(hours=4)
        print(pdt)

        # Parse out datetime object into needed formats
        yymmdd = pdt.strftime("%y%m%d")
        hh = pdt.strftime("%H")
        mm = pdt.strftime("%M")
        ss = pdt.strftime("%S")
            
        # Get the path to the right video and the timestamp in the video for the recorded label
        video_path, video_time =  retrieve_video_and_time(camera, label, pdt, video_root_dir, debug)
        if debug:
            print(video_path, video_time)
        
        if video_path and video_time:
            clip = mpy.VideoFileClip(video_path)
            output_label_dir = outputs_dir + "\\" + label
            
            if not os.path.exists(output_label_dir):
                os.makedirs(output_label_dir)
            
            clip.save_frame("{6}\\{0}_{1}_{2}_{3}{4}{5}.png".format(label, camera, yymmdd, hh, mm, ss, output_label_dir), t=video_time)
            clip.reader.close()


# Make reference to directories and other needed paths
video_root_dir = r"D:\5_Data\Transportation\Cameras\SunTrustPark"
labels_fc = r"D:\3_Sandbox_Projects\1806_CobbCounty_PedestrianDetection\Inputs\S123_Labels.gdb\PedestrianCount"
labels_fc_camera_field = "CameraID"
labels_fc_label_field = "degreesaturation"
labels_fc_datetime_field = "PhotoDateTime"
outputs_dir = r"D:\3_Sandbox_Projects\1806_CobbCounty_PedestrianDetection\Work\1_image-exporter\model_inputs"

# Run main
main(labels_fc, labels_fc_camera_field, labels_fc_label_field, labels_fc_datetime_field, video_root_dir, outputs_dir)

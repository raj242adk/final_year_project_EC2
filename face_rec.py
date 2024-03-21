
import numpy as np
import pandas as pd
import cv2

import redis

# insight face
from insightface.app import FaceAnalysis
from sklearn.metrics import pairwise

# time
import time
from datetime import datetime

import os

# connect to Redis
hostname = 'redis-18220.c256.us-east-1-2.ec2.cloud.redislabs.com'
portnumber = 18220
password = 'iqRWpxHl9SC9FuZ7G7Bv82kZ0NBQfSND'

r = redis.StrictRedis(host=hostname,
                      port=portnumber,
                      password=password)


# Retrive Data from Database
def retrive_data(name):
    retrive_dict = r.hgetall(name)
    retrive_series = pd.Series(retrive_dict)
    retrive_series = retrive_series.apply(lambda x: np.frombuffer(x, dtype=np.float32))
    index = retrive_series.index
    index = list(map(lambda x: x.decode(), index))
    retrive_series.index = index
    retrive_df = retrive_series.to_frame().reset_index()
    retrive_df.columns = ['name_role', 'facial_features']
    retrive_df[['Name', 'Role']] = retrive_df['name_role'].apply(lambda x: x.split('@')).apply(pd.Series)
    return retrive_df[['Name', 'Role', 'facial_features']]


# configure face analysis
faceapp = FaceAnalysis(name='buffalo_sc', root='insightface_model', providers=['CPUExecutionProvider'])
faceapp.prepare(ctx_id=0, det_size=(640, 640), det_thresh=0.5)


# Ml search Algorithm
def ml_search_algorithm(dataframe, feature_column, test_vector,
                        name_role=['Name', 'Role'], thresh=0.5):
    """
    consine similarity base search algorithm
    """
    dataframe = dataframe.copy()
    X_list = dataframe[feature_column].tolist()
    x = np.asarray(X_list)

    similar = pairwise.cosine_similarity(x, test_vector.reshape(1, -1))
    similar_arr = np.array(similar).flatten()
    dataframe['cosine'] = similar_arr
    data_filter = dataframe.query(f'cosine >= {thresh}')
    if len(data_filter) > 0:
        data_filter.reset_index(drop=True, inplace=True)
        argmax = data_filter['cosine'].argmax()
        person_name, person_role = data_filter.loc[argmax][['Name', 'Role']]

    else:
        person_name = 'Unknown'
        person_role = 'Unknown'

    return person_name, person_role


##Real time Predection
# we need to save logs for every 1 mins

class RealTimePred:
    def __init__(self):
        self.logs = dict(name=[], role=[], current_time=[])

    def reset_dict(self):
        self.logs = dict(name=[], role=[], current_time=[])

    def saveLogs_redish(self):
        # create a logs dataframe
        dataframe = pd.DataFrame(self.logs)

        # drop the duplicate information
        dataframe.drop_duplicates('name', inplace=True)
        # Push data to redis database
        # encode the data
        name_list = dataframe['name'].tolist()
        role_list = dataframe['role'].tolist()
        current_time = dataframe['current_time'].tolist()
        encoded_data = []

        for name, role, ctime in zip(name_list, role_list, current_time):
            if name != 'Unknown':
                concat_string = f"{name}@{role}:{ctime}"
                encoded_data.append(concat_string)

        if len(encoded_data) > 0:
            r.lpush('attendace:logs', *encoded_data)
        self.reset_dict()

    def face_prediction(self, test_image, dataframe, feature_column, name_role=['Name', 'Role'], thresh=0.5):
        current_time = str(datetime.now())
        # step1:take the test image and apply to insight face
        results = faceapp.get(test_image)
        test_copy = test_image.copy()

        # step2:use for loop and extract each embedding and pass to ml_search algorithm
        for res in results:
            x1, y1, x2, y2 = res['bbox'].astype(int)
            embeddings = res['embedding']
            person_name, person_role = ml_search_algorithm(dataframe,
                                                           feature_column,
                                                           test_vector=embeddings,
                                                           name_role=name_role,
                                                           thresh=thresh)
            if person_name == 'Unknown':
                color = (0, 0, 255)

            else:
                color = (0, 255, 0)

            cv2.rectangle(test_copy, (x1, y1), (x2, y2), color)

            text_gen = person_name

            cv2.putText(test_copy, text_gen, (x1, y1), cv2.FONT_HERSHEY_DUPLEX, 0.7, color, 2)
            cv2.putText(test_copy, current_time, (x1, y2 + 10), cv2.FONT_HERSHEY_DUPLEX, 0.7, color, 2)

            # save info in logs dict
            self.logs['name'].append(person_name)
            self.logs['role'].append(person_role)
            self.logs['current_time'].append(current_time)

        return test_copy


# Registration Form
class RegistrationForm:
    def __init__(self):
        self.sample = 0

    def reset(self):
        self.sample = 0

    def get_embedding(self,frame):
        results = faceapp.get(frame, max_num=1)
        embedding =None
        for res in results:
            self.sample += 1
            x1, y1, x2, y2 = res['bbox'].astype(int)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 1)

            text= f"samples={self.sample}"
            cv2.putText(frame, text,(x1,y1),cv2.FONT_HERSHEY_DUPLEX,0.6,(255,255,0),2)

            embedding = res['embedding']
        return frame, embedding


    def save_data_in_redish_db(self,name,role):

        if name is not None:
            if name.strip()!='':
                key=f'{name}@{role}'
            else:
                return  'name_false'
        else:
            return 'name_false'

        if 'face_embedding.txt' not in os.listdir():
            return 'file_false'






        # step1 load "face embedding.txt"

        x_array=np.loadtxt('face_embedding.txt',dtype=np.float32)


        #step-2: concert into array
        received_sample=int(x_array.size/512)
        x_array=x_array.reshape(received_sample,512)


        #step 3:cal mean embeddings

        x_mean=x_array.mean(axis=0)
        x_mean=x_mean.astype(np.float32)
        x_mean_bytes=x_mean.tobytes()

        #step 4 save this into redish database

        r.hset(name='academy:register',key=key,value=x_mean_bytes)
        os.remove('face_embedding.txt')
        self.reset()

        return True

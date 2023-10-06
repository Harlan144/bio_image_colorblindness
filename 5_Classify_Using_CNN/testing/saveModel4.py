import os
import tensorflow as tf
from tensorflow import keras
from keras import layers
import matplotlib.pyplot as plt
import numpy as np
from tensorflow.keras.applications import ResNet50

"""
This script allows users to test a trained model on a new data, or to use that model to regenerate graphs.

This currently works with the loaded weights from SavesModel4. 
Run Loaded Weights from SavesModel4 to confirm values and generate new graphs.
"""
base_model = ResNet50(weights='imagenet', 
                             input_shape=(180, 180, 3),
                             include_top=False)

base_model.trainable = False

#This image size worked fine with ResNet50
image_size= (180,180)



data_augmentation = keras.Sequential(
    [
        layers.RandomFlip("horizontal"),
        layers.RandomRotation(0.1)
    ]
)

"""
Copied code from classifycvd4.py so it can call model.evaluate on loaded 
"""

def make_model(input_shape, output_bias):
    output_bias = tf.keras.initializers.Constant(output_bias) #Decreases loss during first few epochs
    
    inputs = keras.Input(shape=input_shape)

    x = data_augmentation(inputs) #apply augmentation
    x = layers.Rescaling(1./255)(x) #Rescale RGB pixels to be (0,1)

    x = base_model(x, training=False) #Call ResNet50 model.

    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dropout(0.3)(x) #Decreases overfitting

    outputs = layers.Dense(1, activation="sigmoid",bias_initializer=output_bias)(x)
    return keras.Model(inputs, outputs)


#Only use test_ds for confirming the model's validity.
test_ds = tf.keras.preprocessing.image_dataset_from_directory(
    "TestImages/",
    image_size=image_size,
    shuffle=True
)


class_weight = {0:0, 1:0}
y = np.concatenate([y for x, y in test_ds], axis=0)
total = 0
for i in y:
    if int(i) in class_weight:
        class_weight[int(i)]+=1
        total+=1
    else:
        print("Error:",i)

#Weigh the classes (friendly or not friendly) according to their prevelance in our test dataset
initial_bias = np.log([class_weight[1]/class_weight[0]]) 

model = make_model(input_shape=image_size + (3,) , output_bias=initial_bias) #Call our model defined above

METRICS = [
      keras.metrics.TruePositives(name='tp'),
      keras.metrics.FalsePositives(name='fp'),
      keras.metrics.TrueNegatives(name='tn'),
      keras.metrics.FalseNegatives(name='fn'), 
      keras.metrics.BinaryAccuracy(name='accuracy'),
      keras.metrics.Precision(name='precision'),
      keras.metrics.Recall(name='recall'),
      keras.metrics.AUC(name='auc'),
      keras.metrics.AUC(name='prc', curve='PR'), # precision-recall curve
]

model.compile(
    optimizer=keras.optimizers.Adam(1e-3),
    loss="binary_crossentropy",
    metrics=METRICS,
)

model.load_weights("SavesModel4/save_at_32.h5") #Call the last save in Model4


score = model.evaluate(test_ds)[1:] #Return the evaluated metrics
for i in range(len(score)):
    print(METRICS[i], score[i])
